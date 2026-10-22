//! Áudio de verdade: microfone, caixa de som e o microfone virtual de cada sistema.
//!
//!   Linux    PulseAudio/PipeWire: cria uma saída "muda" (Praxis interno) e uma entrada
//!            remapeada a partir dela ("Praxis Mic"); no bilateral, a saída "Praxis Speaker",
//!            onde o app de chamada toca a outra pessoa — sem instalar driver
//!   macOS    BlackHole (o instalador do Praxis instala)
//!   Windows  VB-Audio Virtual Cable (o instalador do Praxis instala)
//!
//! Os nomes e a ordem de preferência são os mesmos do Praxis em Python.

use std::collections::VecDeque;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::Sender;
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;
use std::time::Duration;

use anyhow::{anyhow, Context, Result};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};

use crate::vad::{CHUNK, SR};

/// Muda a taxa de amostragem com um filtro passa-baixa (sinc com janela de Hann), em
/// fluxo contínuo. Mais limpo que a interpolação linear do Python ao reduzir de 48 kHz.
pub struct Resampler {
    step: f64,    // amostras de entrada por amostra de saída
    t: f64,       // posição absoluta (em amostras de entrada) da próxima saída
    buf: Vec<f32>,
    offset: usize, // posição absoluta de buf[0]
    taps: isize,
    cutoff: f64,  // frequência de corte, em fração da metade da taxa de entrada
}

impl Resampler {
    pub fn new(src: u32, dst: u32) -> Self {
        let ratio = dst as f64 / src as f64;
        Self { step: 1.0 / ratio, t: 0.0, buf: vec![], offset: 0, taps: 16, cutoff: ratio.min(1.0) * 0.95 }
    }

    fn sample_at(&self, center: f64) -> f32 {
        let ci = center.floor() as isize;
        let (mut acc, mut wsum) = (0.0f64, 0.0f64);
        for k in (ci - self.taps + 1)..=(ci + self.taps) {
            let x = center - k as f64;
            let a = std::f64::consts::PI * x * self.cutoff;
            let sinc = if x.abs() < 1e-9 { 1.0 } else { a.sin() / a };
            let win = 0.5 + 0.5 * (std::f64::consts::PI * x / (self.taps as f64 + 1.0)).cos();
            let w = sinc * win;
            wsum += w;
            if k >= self.offset as isize && ((k as usize) - self.offset) < self.buf.len() {
                acc += self.buf[k as usize - self.offset] as f64 * w;
            }
        }
        (if wsum.abs() > 1e-9 { acc / wsum } else { 0.0 }) as f32
    }

    pub fn process(&mut self, input: &[f32]) -> Vec<f32> {
        if (self.step - 1.0).abs() < 1e-12 {
            return input.to_vec();
        }
        self.buf.extend_from_slice(input);
        let end = (self.offset + self.buf.len()) as f64;
        let mut out = Vec::with_capacity((input.len() as f64 / self.step) as usize + 2);
        // só calcula quando já tem as amostras da direita do filtro
        while self.t + (self.taps as f64) < end {
            out.push(self.sample_at(self.t));
            self.t += self.step;
        }
        // descarta o que nenhuma saída futura vai usar
        let keep_from = (self.t.floor() as isize - self.taps).max(self.offset as isize) as usize;
        let drop = keep_from - self.offset;
        if drop > 0 {
            self.buf.drain(..drop.min(self.buf.len()));
            self.offset += drop;
        }
        out
    }
}

/// Converte de uma vez (para áudio já pronto, como a voz sintetizada).
pub fn resample_all(x: &[f32], src: u32, dst: u32) -> Vec<f32> {
    if src == dst {
        return x.to_vec();
    }
    let mut r = Resampler::new(src, dst);
    let mut out = r.process(x);
    out.extend(r.process(&vec![0.0; 64]));
    out.truncate((x.len() as f64 * dst as f64 / src as f64).round() as usize);
    out
}

fn host() -> cpal::Host {
    cpal::default_host()
}

pub fn list_inputs() -> Vec<String> {
    host().input_devices().map(|d| d.map(|x| x.to_string()).collect()).unwrap_or_default()
}

pub fn list_outputs() -> Vec<String> {
    host().output_devices().map(|d| d.map(|x| x.to_string()).collect()).unwrap_or_default()
}

fn find_input(name: Option<&str>) -> Result<cpal::Device> {
    let h = host();
    match name {
        None => h.default_input_device().ok_or_else(|| anyhow!("nenhum microfone encontrado")),
        Some(n) => h
            .input_devices()?
            .find(|d| d.to_string() == n)
            .or_else(|| h.input_devices().ok()?.find(|d| d.to_string().contains(n)))
            .ok_or_else(|| anyhow!("microfone \"{n}\" não encontrado")),
    }
}

fn find_output(name: Option<&str>) -> Result<cpal::Device> {
    let h = host();
    match name {
        None => h.default_output_device().ok_or_else(|| anyhow!("nenhuma saída de áudio encontrada")),
        Some(n) => h
            .output_devices()?
            .find(|d| d.to_string() == n)
            .or_else(|| h.output_devices().ok()?.find(|d| d.to_string().contains(n)))
            .ok_or_else(|| anyhow!("saída de áudio \"{n}\" não encontrada")),
    }
}

/// Microfone → blocos de 32 ms, mono, 16 kHz. A captura roda numa tarefa própria
/// (o fluxo de áudio do sistema precisa viver na tarefa que o criou).
pub fn spawn_capture(device: Option<String>, tx: Sender<Vec<f32>>, stop: Arc<AtomicBool>) -> Result<JoinHandle<()>> {
    let (ready_tx, ready_rx) = std::sync::mpsc::channel::<Result<()>>();
    let h = std::thread::spawn(move || {
        let start = || -> Result<cpal::Stream> {
            let dev = find_input(device.as_deref())?;
            let sup = dev.default_input_config().context("configuração do microfone")?;
            let (ch, rate, fmt) = (sup.channels() as usize, sup.sample_rate(), sup.sample_format());
            let state = Arc::new(Mutex::new((Resampler::new(rate, SR as u32), Vec::<f32>::new())));
            let push = move |mono: Vec<f32>| {
                let mut st = state.lock().unwrap();
                let out = st.0.process(&mono);
                st.1.extend(out);
                while st.1.len() >= CHUNK {
                    let chunk: Vec<f32> = st.1.drain(..CHUNK).collect();
                    let _ = tx.send(chunk);
                }
            };
            let cfg = sup.config();
            // qualquer formato da placa (16 ou 32 bits inteiros, ponto flutuante…): a média dos
            // canais em f32 (placas profissionais, como a Scarlett, usam 32 bits inteiros)
            fn input<T: cpal::SizedSample>(dev: &cpal::Device, cfg: cpal::StreamConfig, ch: usize,
                    mut push: impl FnMut(Vec<f32>) + Send + 'static) -> Result<cpal::Stream>
            where f32: cpal::FromSample<T> {
                Ok(dev.build_input_stream(cfg, move |d: &[T], _: &_| {
                    push(d.chunks(ch).map(|f| f.iter().map(|&x| x.to_sample::<f32>()).sum::<f32>() / ch as f32).collect())
                }, |e| eprintln!("microfone: {e}"), None)?)
            }
            use cpal::SampleFormat as F;
            let stream = match fmt {
                F::F32 => input::<f32>(&dev, cfg, ch, push)?,
                F::I16 => input::<i16>(&dev, cfg, ch, push)?,
                F::I32 => input::<i32>(&dev, cfg, ch, push)?,
                F::U16 => input::<u16>(&dev, cfg, ch, push)?,
                F::I8 => input::<i8>(&dev, cfg, ch, push)?,
                F::U8 => input::<u8>(&dev, cfg, ch, push)?,
                F::F64 => input::<f64>(&dev, cfg, ch, push)?,
                other => return Err(anyhow!("formato de áudio do microfone não suportado: {other:?}")),
            };
            stream.play()?;
            Ok(stream)
        };
        match start() {
            Ok(stream) => {
                let _ = ready_tx.send(Ok(()));
                while !stop.load(Ordering::Relaxed) {
                    std::thread::sleep(Duration::from_millis(100));
                }
                drop(stream);
            }
            Err(e) => {
                let _ = ready_tx.send(Err(e));
            }
        }
    });
    ready_rx.recv().map_err(|_| anyhow!("a captura do microfone parou"))??;
    Ok(h)
}

/// Uma saída de áudio aberta (a fila é tocada pelo sistema; `play` espera terminar).
pub struct OutputDevice {
    queue: Arc<Mutex<VecDeque<f32>>>,
    rate: u32,
    _keep: Arc<AtomicBool>,
}

impl OutputDevice {
    pub fn open(name: Option<String>) -> Result<Arc<Self>> {
        let queue = Arc::new(Mutex::new(VecDeque::<f32>::new()));
        let keep = Arc::new(AtomicBool::new(true));
        let (ready_tx, ready_rx) = std::sync::mpsc::channel::<Result<u32>>();
        let (q, k) = (queue.clone(), keep.clone());
        std::thread::spawn(move || {
            let start = || -> Result<(cpal::Stream, u32)> {
                let dev = find_output(name.as_deref())?;
                let sup = dev.default_output_config().context("configuração da saída de áudio")?;
                let (ch, rate, fmt) = (sup.channels() as usize, sup.sample_rate(), sup.sample_format());
                let cfg = sup.config();
                let q2 = q.clone();
                // qualquer formato da placa: a mesma amostra em todos os canais
                fn output<T: cpal::SizedSample + cpal::FromSample<f32>>(dev: &cpal::Device, cfg: cpal::StreamConfig,
                        ch: usize, q: Arc<Mutex<VecDeque<f32>>>) -> Result<cpal::Stream> {
                    Ok(dev.build_output_stream(cfg, move |d: &mut [T], _: &_| {
                        let mut qq = q.lock().unwrap();
                        for f in d.chunks_mut(ch) {
                            let v = T::from_sample(qq.pop_front().unwrap_or(0.0).clamp(-1.0, 1.0));
                            f.iter_mut().for_each(|x| *x = v);
                        }
                    }, |e| eprintln!("saída de áudio: {e}"), None)?)
                }
                    use cpal::SampleFormat as F;
                let stream = match fmt {
                    F::F32 => output::<f32>(&dev, cfg, ch, q2)?,
                    F::I16 => output::<i16>(&dev, cfg, ch, q2)?,
                    F::I32 => output::<i32>(&dev, cfg, ch, q2)?,
                    F::U16 => output::<u16>(&dev, cfg, ch, q2)?,
                    F::I8 => output::<i8>(&dev, cfg, ch, q2)?,
                    F::U8 => output::<u8>(&dev, cfg, ch, q2)?,
                    F::F64 => output::<f64>(&dev, cfg, ch, q2)?,
                    other => return Err(anyhow!("formato da saída de áudio não suportado: {other:?}")),
                };
                stream.play()?;
                Ok((stream, rate))
            };
            match start() {
                Ok((stream, rate)) => {
                    let _ = ready_tx.send(Ok(rate));
                    while k.load(Ordering::Relaxed) {
                        std::thread::sleep(Duration::from_millis(100));
                    }
                    drop(stream);
                }
                Err(e) => {
                    let _ = ready_tx.send(Err(e));
                }
            }
        });
        let rate = ready_rx.recv().map_err(|_| anyhow!("a saída de áudio parou"))??;
        Ok(Arc::new(Self { queue, rate, _keep: keep }))
    }

    fn enqueue(&self, samples: &[f32], sr: u32) -> f32 {
        let x = resample_all(samples, sr, self.rate);
        let dur = x.len() as f32 / self.rate as f32;
        self.queue.lock().unwrap().extend(x);
        dur
    }

    fn pending_s(&self) -> f32 {
        self.queue.lock().unwrap().len() as f32 / self.rate as f32
    }
}

impl Drop for OutputDevice {
    fn drop(&mut self) {
        self._keep.store(false, Ordering::Relaxed);
    }
}

/// Toca em uma ou mais saídas ao mesmo tempo (ex.: microfone virtual + fone para ouvir).
/// Saídas que tocam juntas; o segundo campo é o sinal de parar: ao parar ou fechar, o som
/// em fila é descartado na hora (antes, fechar esperava terminar de tocar tudo).
pub struct Speakers(pub Vec<Arc<OutputDevice>>, pub Arc<AtomicBool>);

impl crate::pipeline::Speaker for Speakers {
    fn play(&self, samples: &[f32], sample_rate: u32) {
        for o in &self.0 {
            o.enqueue(samples, sample_rate);
        }
        // espera todas terminarem (como um alto-falante de verdade), ou até mandarem parar
        while self.0.iter().any(|o| o.pending_s() > 0.0) {
            if self.1.load(Ordering::Relaxed) {
                self.0.iter().for_each(|o| o.queue.lock().unwrap().clear());
                return;
            }
            std::thread::sleep(Duration::from_millis(10));
        }
    }
}

// ── Microfone virtual ─────────────────────────────────────────────────────────

pub const SINK_OUT: &str = "Praxis_Out";
pub const SRC_MIC: &str = "Praxis_Mic";
/// nomes que o usuário vê no app de chamada
pub const SRC_DESC: &str = "Praxis Mic";
pub const SINK_IN: &str = "Praxis_In";
pub const SINK_IN_DESC: &str = "Praxis Speaker";
pub const SINK_OUT_DESC: &str = "Praxis interno";

/// (trecho do nome do lado onde o Praxis toca, trecho do nome que o app de chamada grava)
pub const LOOPBACK_DRIVERS: [(&str, &str); 6] = [
    ("BlackHole 2ch", "BlackHole 2ch"),
    ("BlackHole", "BlackHole"),
    ("CABLE Input", "CABLE Output"),
    ("VoiceMeeter Input", "VoiceMeeter Output"),
    ("Loopback Audio", "Loopback Audio"),
    ("Soundflower (2ch)", "Soundflower (2ch)"),
];
/// Segundo cabo, para o modo bilateral (saída do app de chamada → Praxis)
pub const PEER_LOOPBACK_DRIVERS: [(&str, &str); 3] = [
    ("BlackHole 16ch", "BlackHole 16ch"),
    ("CABLE-A Input", "CABLE-A Output"),
    ("VoiceMeeter Aux Input", "VoiceMeeter Aux Output"),
];

#[derive(Debug, Default)]
pub struct VirtualMic {
    /// saída onde o Praxis toca a fala traduzida
    pub target: Option<String>,
    /// o que o usuário escolhe como microfone no app de chamada
    pub mic_label: String,
    /// de onde vem a fala da outra pessoa (bilateral)
    pub peer_capture: Option<String>,
    /// para onde o usuário manda a saída do app de chamada (bilateral)
    pub peer_label: String,
    pulse_modules: Vec<u32>,
}

/// "sink_properties='device.description=\"Praxis Mic\"'": as aspas deixam o nome ter espaço
fn props(kind: &str, desc: &str) -> String {
    format!("{kind}_properties='device.description=\"{desc}\"'")
}

fn pactl(args: &[&str]) -> Result<String> {
    let out = std::process::Command::new("pactl").args(args).output().context("pactl")?;
    if !out.status.success() {
        return Err(anyhow!("pactl {}: {}", args.join(" "), String::from_utf8_lossy(&out.stderr)));
    }
    Ok(String::from_utf8_lossy(&out.stdout).trim().to_string())
}

impl VirtualMic {
    pub fn setup(bilateral: bool) -> Result<Self> {
        let mut vm = VirtualMic::default();
        if cfg!(target_os = "linux") && which("pactl") {
            // sobras de uma execução que terminou à força (travou, foi morta): sem isto os
            // dispositivos se duplicam a cada abertura
            if let Ok(mods) = pactl(&["list", "short", "modules"]) {
                for line in mods.lines() {
                    let ours = [format!("sink_name={SINK_OUT} "), format!("sink_name={SINK_IN} "), format!("source_name={SRC_MIC} ")]
                        .iter().any(|k| format!("{line} ").contains(k.as_str()));
                    if let (true, Some(id)) = (ours, line.split_whitespace().next()) {
                        let _ = pactl(&["unload-module", id]);
                    }
                }
            }
            let mut load = |args: &[&str]| -> Result<()> {
                let id: u32 = pactl(&[&["load-module"], args].concat())?.parse().unwrap_or(0);
                vm.pulse_modules.push(id);
                Ok(())
            };
            load(&["module-null-sink", &format!("sink_name={SINK_OUT}"), &props("sink", SINK_OUT_DESC)])?;
            load(&["module-remap-source", &format!("source_name={SRC_MIC}"), &format!("master={SINK_OUT}.monitor"),
                   &props("source", SRC_DESC)])?;
            if bilateral {
                load(&["module-null-sink", &format!("sink_name={SINK_IN}"), &props("sink", SINK_IN_DESC)])?;
            }
            // o sistema lista as saídas pelo nome de exibição, não pelo nome técnico
            vm.target = Some(SINK_OUT_DESC.into());
            vm.mic_label = SRC_DESC.into();
            if bilateral {
                // o sistema lista a gravação da saída pelo nome de exibição ("Monitor of
                // Praxis Speaker"), não pelo nome técnico (Praxis_In.monitor)
                vm.peer_capture = Some(SINK_IN_DESC.into());
                vm.peer_label = SINK_IN_DESC.into();
            }
            return Ok(vm);
        }
        let outs = list_outputs();
        let ins = list_inputs();
        let pick = |table: &[(&str, &str)]| {
            table.iter().find_map(|(o, i)| {
                let out = outs.iter().find(|n| n.contains(o))?;
                let inp = ins.iter().find(|n| n.contains(i)).cloned().unwrap_or_else(|| i.to_string());
                Some((out.clone(), inp))
            })
        };
        let (target, label) = pick(&LOOPBACK_DRIVERS).ok_or_else(|| anyhow!(if cfg!(target_os = "macos") {
            "microfone virtual não encontrado: instale o BlackHole (o instalador do Praxis faz isso)"
        } else {
            "microfone virtual não encontrado: instale o VB-Audio Virtual Cable (o instalador do Praxis faz isso)"
        }))?;
        vm.target = Some(target);
        vm.mic_label = label;
        if bilateral {
            let (peer_out, peer_in) = pick(&PEER_LOOPBACK_DRIVERS)
                .ok_or_else(|| anyhow!("o modo bilateral precisa de um segundo cabo de áudio virtual (BlackHole 16ch ou CABLE-A)"))?;
            vm.peer_capture = Some(peer_in);
            vm.peer_label = peer_out;
        }
        Ok(vm)
    }

    /// Remove os dispositivos virtuais criados (Linux). Chamado sempre ao parar.
    pub fn teardown(&mut self) {
        for id in self.pulse_modules.drain(..).rev() {
            let _ = pactl(&["unload-module", &id.to_string()]);
        }
    }
}

impl Drop for VirtualMic {
    fn drop(&mut self) {
        self.teardown();
    }
}

fn which(cmd: &str) -> bool {
    std::env::var_os("PATH")
        .map(|p| std::env::split_paths(&p).any(|d| d.join(cmd).is_file()))
        .unwrap_or(false)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tone(freq: f32, sr: u32, secs: f32) -> Vec<f32> {
        (0..(sr as f32 * secs) as usize).map(|i| (2.0 * std::f32::consts::PI * freq * i as f32 / sr as f32).sin()).collect()
    }

    fn rms(x: &[f32]) -> f32 {
        (x.iter().map(|v| v * v).sum::<f32>() / x.len().max(1) as f32).sqrt()
    }

    #[test]
    fn reamostragem_mantem_a_fala_e_corta_o_que_nao_cabe() {
        // 1 kHz (faixa da voz) passa; 7,5 kHz não cabe em 16 kHz e não pode virar ruído
        let fala = resample_all(&tone(1000.0, 48_000, 1.0), 48_000, 16_000);
        assert!((fala.len() as i32 - 16_000).abs() <= 2);
        assert!(rms(&fala[1000..15000]) > 0.6, "a fala precisa passar: {}", rms(&fala[1000..15000]));
        let agudo = resample_all(&tone(9000.0, 48_000, 1.0), 48_000, 16_000);
        assert!(rms(&agudo[1000..15000]) < 0.1, "o que não cabe não pode virar ruído: {}", rms(&agudo[1000..15000]));
    }

    #[test]
    fn reamostragem_em_blocos_igual_de_uma_vez() {
        let x = tone(440.0, 44_100, 0.5);
        let mut r = Resampler::new(44_100, 16_000);
        let mut aos_poucos = vec![];
        for c in x.chunks(441) {
            aos_poucos.extend(r.process(c));
        }
        let inteiro = resample_all(&x, 44_100, 16_000);
        let n = aos_poucos.len().min(inteiro.len()) - 50;
        let diff: f32 = (100..n).map(|i| (aos_poucos[i] - inteiro[i]).abs()).fold(0.0, f32::max);
        assert!(diff < 1e-3, "processar em blocos tem de dar o mesmo resultado: {diff}");
    }

    #[test]
    fn subir_a_taxa_tambem_funciona() {
        let y = resample_all(&tone(440.0, 16_000, 0.5), 16_000, 48_000);
        assert!((y.len() as i32 - 24_000).abs() <= 3);
        assert!(rms(&y[2000..22000]) > 0.6);
    }
}
