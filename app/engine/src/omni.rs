//! OmniVoice (k2-fsa) pelo onnxruntime, sem PyTorch: o clonador da versão antiga do Praxis.
//! Pacote e especificação: LEIAME-RUST.md do pacote OmniVoice do Praxis.
//! Primeira etapa: carregar o modelo de linguagem no processador ou na placa de vídeo do Mac
//! (CoreML) e medir um passo.

use std::path::Path;

use anyhow::{anyhow, bail, Result};

/// Onde roda o modelo
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Placa {
    Processador,
    /// Mac: CoreML (a placa pelo Metal, ou o processador quando a peça não cabe nela)
    CoreMlPlaca,
}

pub fn sessao(modelo: &Path, placa: Placa, threads: usize) -> Result<ort::session::Session> {
    let env = crate::vad::ort_env()?;
    let e = |x: &dyn std::fmt::Display| anyhow!("OmniVoice: {x}");
    let mut b = ort::session::Session::builder(env).map_err(|x| e(&x))?.with_intra_threads(threads).map_err(|x| e(&x))?;
    // experimento: PRAXIS_OMNI_S=<comprimento> fixa o tamanho do pedido (o CoreML só põe o modelo
    // inteiro na placa com tamanhos fixos)
    if let Some(n) = std::env::var("PRAXIS_OMNI_S").ok().and_then(|v| v.parse::<i64>().ok()) {
        for (nome, v) in [("B", 1), ("S", n), ("S2", n)] {
            b = b.with_dimension_override(nome, v).map_err(|x| e(&x))?;
        }
    }
    if placa == Placa::CoreMlPlaca {
        #[cfg(target_os = "macos")]
        {
            use ort::ep::coreml::{ComputeUnits, ModelFormat};
            let cache = std::env::temp_dir().join("praxis-coreml");
            let _ = std::fs::create_dir_all(&cache);
            // experimento: PRAXIS_COREML_FORMATO=nn usa o formato antigo (NeuralNetwork)
            let formato = if std::env::var("PRAXIS_COREML_FORMATO").is_ok_and(|v| v == "nn") { ModelFormat::NeuralNetwork } else { ModelFormat::MLProgram };
            let ep = ort::ep::CoreML::default()
                .with_model_format(formato)
                .with_compute_units(ComputeUnits::CPUAndGPU)
                .with_model_cache_dir(cache.display())
                .build()
                .error_on_failure();
            b = b.with_execution_providers([ep]).map_err(|x| e(&x))?;
        }
        #[cfg(not(target_os = "macos"))]
        bail!("CoreML só existe no Mac");
    }
    b.commit_from_file(modelo).map_err(|x| e(&x))
}

/// Lê um .npy simples (little-endian, ordem C): (forma, bytes dos dados, tipo)
pub fn ler_npy(p: &Path) -> Result<(Vec<usize>, Vec<u8>, String)> {
    let b = std::fs::read(p)?;
    if &b[..6] != b"\x93NUMPY" {
        bail!("{} não é .npy", p.display());
    }
    let (hlen, ini) = if b[6] == 1 { (u16::from_le_bytes([b[8], b[9]]) as usize, 10) } else { (u32::from_le_bytes([b[8], b[9], b[10], b[11]]) as usize, 12) };
    let h = String::from_utf8_lossy(&b[ini..ini + hlen]).to_string();
    let descr = h.split("'descr':").nth(1).and_then(|s| s.split('\'').nth(1)).unwrap_or("").to_string();
    let forma: Vec<usize> = h.split("'shape':").nth(1).and_then(|s| s.split(['(', ')']).nth(1))
        .map(|s| s.split(',').filter_map(|x| x.trim().parse().ok()).collect()).unwrap_or_default();
    Ok((forma, b[ini + hlen..].to_vec(), descr))
}

/// Mede um passo do modelo com o pedido dos vetores de teste; devolve (segundos por passo,
/// maior diferença para a saída de referência do passo 1).
pub fn medir_passo(pacote: &Path, arquivo_llm: &str, placa: Placa, threads: usize, vezes: usize) -> Result<(f64, f32, f64)> {
    let t = pacote.join("testes");
    let (fi, bi, _) = ler_npy(&t.join("04_input_ids.npy"))?;
    let (fm, bm, _) = ler_npy(&t.join("04_audio_mask.npy"))?;
    let (_, bc, _) = ler_npy(&t.join("05_passo1_logits_cond.npy"))?;
    let ids: Vec<i64> = bi.chunks(8).map(|c| i64::from_le_bytes(c.try_into().unwrap())).collect();
    let mask: Vec<bool> = bm.iter().map(|&x| x != 0).collect();
    let refc: Vec<f32> = bc.chunks(4).map(|c| f32::from_le_bytes(c.try_into().unwrap())).collect();
    let s = fi[2];
    let carga = std::time::Instant::now();
    let mut sess = sessao(&pacote.join(arquivo_llm), placa, threads)?;
    let carga = carga.elapsed().as_secs_f64();
    let m = |x: ort::Error| anyhow!("OmniVoice: {x}");
    let mut dif = 0f32;
    let mut tempos = vec![];
    for k in 0..vezes {
        let a = ort::value::Tensor::from_array((fi.clone(), ids.clone())).map_err(m)?;
        let b = ort::value::Tensor::from_array((fm.clone(), mask.clone())).map_err(m)?;
        let c = ort::value::Tensor::from_array((vec![1usize, 1, s, s], vec![true; s * s])).map_err(m)?;
        let t0 = std::time::Instant::now();
        let out = sess.run(ort::inputs!["input_ids" => a, "audio_mask" => b, "attention_mask" => c]).map_err(m)?;
        tempos.push(t0.elapsed().as_secs_f64());
        if k == 0 {
            let (shape, logits) = out["logits"].try_extract_tensor::<f32>().map_err(m)?;
            // logits [1, 8, S, 1025]; referência: os últimos T quadros [8, T, 1025]
            let (sl, v) = (shape[2] as usize, shape[3] as usize);
            let tq = refc.len() / (8 * v);
            for cb in 0..8 {
                for q in 0..tq {
                    for j in 0..v {
                        let x = logits[(cb * sl + (sl - tq + q)) * v + j];
                        dif = dif.max((x - refc[(cb * tq + q) * v + j]).abs());
                    }
                }
            }
        }
    }
    tempos.sort_by(|a, b| a.total_cmp(b));
    Ok((tempos[tempos.len() / 2], dif, carga))
}

// ── OmniVoice pelo omnivoice.cpp (ggml): Vulkan, Metal, CUDA ou processador ─────────────────
//
// A biblioteca (libomnivoice) é carregada na hora. A voz usa uma referência curta (4–6 s) da
// gravação do usuário — ou o trecho que ele acabou de falar, como o Praxis antigo —
// transformada uma vez em códigos de voz e reaproveitada em cada frase.

use std::ffi::{c_char, c_int, c_void, CStr, CString};
use std::sync::Mutex;

#[repr(C)]
struct OvAudio { samples: *mut f32, n_samples: c_int, sample_rate: c_int, channels: c_int }
#[repr(C)]
struct OvInitParams { abi_version: c_int, model_path: *const c_char, codec_path: *const c_char, use_fa: bool, clamp_fp16: bool, device: *const c_char }
#[repr(C)]
struct OvTtsParams {
    abi_version: c_int,
    text: *const c_char,
    lang: *const c_char,
    instruct: *const c_char,
    t_override: c_int,
    chunk_duration_sec: f32,
    chunk_threshold_sec: f32,
    denoise: bool,
    preprocess_prompt: bool,
    mg_num_step: c_int,
    mg_guidance_scale: f32,
    mg_t_shift: f32,
    mg_layer_penalty_factor: f32,
    mg_position_temperature: f32,
    mg_class_temperature: f32,
    mg_seed: u64,
    ref_audio_tokens: *const i32,
    ref_t: c_int,
    ref_audio_24k: *const f32,
    ref_n_samples: c_int,
    ref_text: *const c_char,
    dump_dir: *const c_char,
    cancel: *const c_void,
    cancel_user_data: *mut c_void,
    on_chunk: *const c_void,
    on_chunk_user_data: *mut c_void,
    postproc: bool,
}
#[repr(C)]
struct OvVoiceRef { ref_codes: *mut i32, ref_t: c_int, num_codebooks: c_int }

struct Funcs {
    init_default: unsafe extern "C" fn(*mut OvInitParams),
    init: unsafe extern "C" fn(*const OvInitParams) -> *mut c_void,
    free: unsafe extern "C" fn(*mut c_void),
    last_error: unsafe extern "C" fn() -> *const c_char,
    tts_default: unsafe extern "C" fn(*mut OvTtsParams),
    synthesize: unsafe extern "C" fn(*mut c_void, *const OvTtsParams, *mut OvAudio) -> c_int,
    audio_free: unsafe extern "C" fn(*mut OvAudio),
    extract_ref: unsafe extern "C" fn(*mut c_void, *const f32, c_int, *mut OvVoiceRef) -> c_int,
    ref_free: unsafe extern "C" fn(*mut OvVoiceRef),
}

/// Referência de voz já codificada
#[derive(Clone)]
struct Referencia { codigos: Vec<i32>, t: c_int, texto: CString }

pub struct OmniVoice {
    /// Mac com duas placas: a AMD fica ligada enquanto o OmniVoice existe
    _placa: Option<PlacaLigada>,
    _lib: libloading::Library,
    f: Funcs,
    ctx: Mutex<*mut c_void>,
    referencia: Mutex<Option<Referencia>>,
    /// quando a referência ao vivo foi trocada (no máximo a cada 10 s: codificar leva ~1,5 s de placa)
    trocada: Mutex<Option<std::time::Instant>>,
    /// referência da gravação (volta a ela quando não há trecho ao vivo)
    fixa: Mutex<Option<Referencia>>,
    pub passos: i32,
    pub dispositivo: String,
    /// segundos de cálculo por segundo de fala medidos nesta placa (0 = ainda não medido)
    pub rtf: Mutex<f32>,
}

unsafe impl Send for OmniVoice {}
unsafe impl Sync for OmniVoice {}

/// Passos de geração. Medido (23/10/2026, Radeon Pro 5500M pelo Vulkan, modelo de 8 bits): 8 passos
/// 0,81 s por segundo de fala, 6 passos 0,63, 4 passos 0,44, com a frase reconhecida igual. O
/// modelo de 4 bits sai quebrado nessa placa.
/// 8. Medido (23/10/2026, voz do usuário, 14 frases em inglês, reconhecidas pelo Parakeet): 4 e
/// 6 passos 9,1% de palavras erradas (engole palavras), 8 passos 0%. Na Radeon Pro 5500M, 8 passos
/// gastam ~1 s de cálculo por segundo de fala.
pub const PASSOS: i32 = 8;

/// Acima disto (segundos de cálculo por segundo de fala, 8 passos) a placa não dá conta da
/// tradução simultânea com a voz fiel. Medido: RTX 3050 ~0,2 (simultâneo); Radeon Pro 5500M
/// ~0,8–1,0 (atraso de 5 s ou mais). Na escolha automática, acima disto vai a voz leve.
pub const RTF_SIMULTANEO: f32 = 0.5;

/// Desempenho medido desta placa com o OmniVoice (segundos de cálculo por segundo de fala)
pub fn desempenho_guardado(store: &crate::models::ModelStore) -> Option<f32> {
    let v: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(store.omnivoice_dir().join("desempenho.json")).ok()?).ok()?;
    (v["passos"].as_i64() == Some(PASSOS as i64)).then(|| v["rtf"].as_f64().map(|x| x as f32)).flatten()
}

pub fn guardar_desempenho(store: &crate::models::ModelStore, dispositivo: &str, rtf: f32) {
    let v = serde_json::json!({"dispositivo": dispositivo, "passos": PASSOS, "rtf": rtf});
    let _ = std::fs::write(store.omnivoice_dir().join("desempenho.json"), v.to_string());
}

/// Nome da biblioteca ao lado do programa (ou PRAXIS_OMNIVOICE_LIB)
pub fn caminho_biblioteca() -> std::path::PathBuf {
    if let Ok(p) = std::env::var("PRAXIS_OMNIVOICE_LIB") {
        return p.into();
    }
    let nome = if cfg!(target_os = "windows") { "omnivoice.dll" } else if cfg!(target_os = "macos") { "libomnivoice.dylib" } else { "libomnivoice.so" };
    let dir = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.to_path_buf())).unwrap_or_default();
    dir.join("omnivoice").join(nome)
}

/// Placa preferida para o OmniVoice: Vulkan (AMD/Intel, e AMD no Mac pelo MoltenVK), Metal nos
/// Macs com chip Apple, CUDA na NVIDIA. PRAXIS_OMNIVOICE_DISPOSITIVO escolhe outro.
pub fn dispositivo_preferido() -> String {
    if let Ok(d) = std::env::var("PRAXIS_OMNIVOICE_DISPOSITIVO") {
        return d;
    }
    if cfg!(all(target_os = "macos", target_arch = "aarch64")) { "MTL0".into() } else { "Vulkan0".into() }
}

impl OmniVoice {
    /// `modelo`: omnivoice-base-*.gguf; `codec`: omnivoice-tokenizer-*.gguf
    pub fn carregar(modelo: &Path, codec: &Path, dispositivo: &str, passos: i32) -> Result<Self> {
        // Mac: o Vulkan vai pelo MoltenVK que acompanha o Praxis (pasta omnivoice/)
        // na placa de vídeo, 2 linhas no processador bastam (mais só disputam com o reconhecimento)
        if !dispositivo.starts_with("CPU") && std::env::var_os("OMNIVOICE_THREADS").is_none() {
            unsafe { std::env::set_var("OMNIVOICE_THREADS", "2") };
        }
        let icd = caminho_biblioteca().with_file_name("MoltenVK_icd.json");
        if icd.exists() && std::env::var_os("VK_ICD_FILENAMES").is_none() {
            unsafe { std::env::set_var("VK_ICD_FILENAMES", &icd) };
        }
        unsafe {
            let lib = libloading::Library::new(caminho_biblioteca())
                .map_err(|e| anyhow!("biblioteca do OmniVoice ({}): {e}", caminho_biblioteca().display()))?;
            macro_rules! sym { ($n:literal) => { *lib.get($n).map_err(|e| anyhow!("OmniVoice: {e}"))? } }
            let f = Funcs {
                init_default: sym!(b"ov_init_default_params\0"),
                init: sym!(b"ov_init\0"),
                free: sym!(b"ov_free\0"),
                last_error: sym!(b"ov_last_error\0"),
                tts_default: sym!(b"ov_tts_default_params\0"),
                synthesize: sym!(b"ov_synthesize\0"),
                audio_free: sym!(b"ov_audio_free\0"),
                extract_ref: sym!(b"ov_extract_voice_ref\0"),
                ref_free: sym!(b"ov_voice_ref_free\0"),
            };
            let m = CString::new(modelo.to_string_lossy().as_bytes())?;
            let c = CString::new(codec.to_string_lossy().as_bytes())?;
            let d = CString::new(dispositivo)?;
            let mut p: OvInitParams = std::mem::zeroed();
            (f.init_default)(&mut p);
            p.model_path = m.as_ptr();
            p.codec_path = c.as_ptr();
            // medido na AMD (Vulkan): a atenção rápida deixa cada passo 2× mais lento
            p.use_fa = false;
            p.device = d.as_ptr();
            let ctx = (f.init)(&p);
            if ctx.is_null() {
                bail!("OmniVoice não carregou: {}", CStr::from_ptr((f.last_error)()).to_string_lossy());
            }
            let placa = if dispositivo.starts_with("CPU") { None } else { PlacaLigada::pedir() };
            Ok(Self { _placa: placa, _lib: lib, f, ctx: Mutex::new(ctx), referencia: Mutex::new(None), trocada: Mutex::new(None), fixa: Mutex::new(None), passos, dispositivo: dispositivo.into(), rtf: Mutex::new(0.0) })
        }
    }

    fn erro(&self) -> String {
        unsafe { CStr::from_ptr((self.f.last_error)()).to_string_lossy().to_string() }
    }

    /// Codifica uma referência (áudio a 16 kHz e o que foi dito nele).
    fn codificar(&self, audio_16k: &[f32], texto: &str) -> Result<Referencia> {
        let a24 = reamostrar(audio_16k, 16_000, 24_000);
        let ctx = self.ctx.lock().unwrap();
        unsafe {
            let mut r: OvVoiceRef = std::mem::zeroed();
            let st = (self.f.extract_ref)(*ctx, a24.as_ptr(), a24.len() as c_int, &mut r);
            if st != 0 || r.ref_codes.is_null() {
                bail!("OmniVoice (referência): {}", self.erro());
            }
            let n = (r.ref_t * r.num_codebooks) as usize;
            let codigos = std::slice::from_raw_parts(r.ref_codes, n).to_vec();
            let t = r.ref_t;
            (self.f.ref_free)(&mut r);
            Ok(Referencia { codigos, t, texto: CString::new(texto)? })
        }
    }

    /// A referência fixa: um trecho da gravação do usuário.
    pub fn definir_referencia(&self, audio_16k: &[f32], texto: &str) -> Result<()> {
        let r = self.codificar(audio_16k, texto)?;
        *self.fixa.lock().unwrap() = Some(r.clone());
        *self.referencia.lock().unwrap() = Some(r);
        // aquece a placa (a 1ª frase compila os programas dela e sai mais lenta)
        let _ = self.falar("Ok.", "en");
        Ok(())
    }

    /// Referência ao vivo: o trecho que o usuário acabou de falar (como o Praxis antigo). Trechos
    /// curtos demais ou sem texto mantêm a anterior.
    pub fn referencia_ao_vivo(&self, audio_16k: &[f32], texto: &str) {
        // desligada por padrão: o trecho do microfone, com o ruído do ambiente, piorava a voz em
        // relação à referência limpa da gravação (23/10/2026). PRAXIS_REF_AO_VIVO=1 liga.
        if !std::env::var("PRAXIS_REF_AO_VIVO").is_ok_and(|v| v == "1") {
            return;
        }
        let s = audio_16k.len() as f32 / 16_000.0;
        if !(2.5..=8.0).contains(&s) || texto.split_whitespace().count() < 4 {
            return;
        }
        if self.trocada.lock().unwrap().is_some_and(|t| t.elapsed().as_secs() < 10) {
            return;
        }
        *self.trocada.lock().unwrap() = Some(std::time::Instant::now());
        if let Ok(r) = self.codificar(audio_16k, texto) {
            *self.referencia.lock().unwrap() = Some(r);
        }
    }

    /// Mede a placa: segundos de cálculo por segundo de fala numa frase de teste em inglês.
    pub fn medir(&self) -> Result<f32> {
        let t = std::time::Instant::now();
        let a = self.falar("Thank you for joining the call, let us start the meeting now.", "en")?;
        let r = t.elapsed().as_secs_f32() / (a.len() as f32 / 24_000.0).max(0.5);
        *self.rtf.lock().unwrap() = r;
        Ok(r)
    }

    /// Menor pedaço da tradução simultânea (palavras). Placa rápida (≤ 0,4 s por segundo de fala,
    /// ex.: RTX 3050 ~0,25): pedaços curtos, a tradução começa enquanto a pessoa fala. Placa lenta
    /// ou não medida: pedaços longos (cada chamada tem um custo fixo e pedaço curto acumula atraso).
    pub fn pedaco_minimo(&self) -> usize {
        let r = *self.rtf.lock().unwrap();
        if r > 0.0 && r <= 0.4 { 6 } else { 16 }
    }

    /// Gera a fala de `texto` em `lang` (código ISO) na voz da referência, a 24 kHz.
    pub fn falar(&self, texto: &str, lang: &str) -> Result<Vec<f32>> {
        self.falar_escala(texto, lang, 1.0)
    }

    /// Como `falar`, com `escala` < 1 falando mais rápido: a duração vem do ritmo da referência
    /// (quadros por letra, como a estimativa do próprio OmniVoice) vezes a escala.
    pub fn falar_escala(&self, texto: &str, lang: &str, escala: f32) -> Result<Vec<f32>> {
        let r = self.referencia.lock().unwrap().clone().or_else(|| self.fixa.lock().unwrap().clone())
            .ok_or_else(|| anyhow!("OmniVoice sem referência de voz"))?;
        let t = CString::new(texto)?;
        let l = CString::new(lang)?;
        let ctx = self.ctx.lock().unwrap();
        unsafe {
            let mut p: OvTtsParams = std::mem::zeroed();
            (self.f.tts_default)(&mut p);
            p.text = t.as_ptr();
            p.lang = l.as_ptr();
            p.mg_num_step = self.passos;
            p.ref_audio_tokens = r.codigos.as_ptr();
            p.ref_t = r.t;
            p.ref_text = r.texto.as_ptr();
            // a duração fica com o próprio OmniVoice: forçar pelo ritmo da referência (outro
            // idioma) fazia a voz correr e soar artificial (23/10/2026)
            let _ = escala;
            let mut out: OvAudio = std::mem::zeroed();
            let st = (self.f.synthesize)(*ctx, &p, &mut out);
            if st != 0 || out.samples.is_null() {
                bail!("OmniVoice: {}", self.erro());
            }
            let v = std::slice::from_raw_parts(out.samples, out.n_samples as usize).to_vec();
            (self.f.audio_free)(&mut out);
            Ok(v)
        }
    }
}

impl Drop for OmniVoice {
    fn drop(&mut self) {
        let ctx = *self.ctx.lock().unwrap();
        unsafe { (self.f.free)(ctx) };
    }
}

/// Troca de taxa simples (interpolação linear) — a referência só precisa do timbre.
pub fn reamostrar(x: &[f32], de: u32, para: u32) -> Vec<f32> {
    if de == para || x.is_empty() {
        return x.to_vec();
    }
    let n = (x.len() as u64 * para as u64 / de as u64) as usize;
    (0..n).map(|i| {
        let pos = i as f64 * de as f64 / para as f64;
        let k = pos as usize;
        let fr = (pos - k as f64) as f32;
        let a = x[k.min(x.len() - 1)];
        let b = x[(k + 1).min(x.len() - 1)];
        a + (b - a) * fr
    }).collect()
}

/// Escolhe na gravação do usuário um trecho de 4 a 6 s que começa e termina em pausa (o
/// OmniVoice "continua" referências cortadas no meio da frase). Devolve (início, fim) em amostras.
pub fn trecho_de_referencia(x: &[f32]) -> (usize, usize) {
    let q = 16_000 / 50; // quadros de 20 ms
    let rms: Vec<f32> = x.chunks(q).map(|c| (c.iter().map(|v| v * v).sum::<f32>() / c.len() as f32).sqrt()).collect();
    let pico = rms.iter().cloned().fold(0f32, f32::max);
    let silencio: Vec<bool> = rms.iter().map(|&r| r < pico * 0.05).collect();
    // pausas: 250 ms ou mais de silêncio; o corte fica no meio da pausa
    let mut cortes = vec![0usize];
    let mut i = 0;
    while i < silencio.len() {
        if silencio[i] {
            let ini = i;
            while i < silencio.len() && silencio[i] { i += 1; }
            if i - ini >= 12 { cortes.push((ini + i) / 2); }
        } else {
            i += 1;
        }
    }
    cortes.push(silencio.len());
    let mut melhor = (0, silencio.len().min(5 * 50));
    let mut dist = f32::MAX;
    for a in 0..cortes.len() {
        for b in a + 1..cortes.len() {
            let s = (cortes[b] - cortes[a]) as f32 / 50.0;
            if (3.5..=6.5).contains(&s) && (s - 5.0).abs() < dist {
                dist = (s - 5.0).abs();
                melhor = (cortes[a], cortes[b]);
            }
        }
    }
    ((melhor.0 * q).min(x.len()), (melhor.1 * q).min(x.len()))
}

/// Mac com duas placas (Intel + AMD): enquanto existir, pede ao macOS que mantenha a placa
/// dedicada ligada. Sem isso, entre uma fala e outra o macOS desliga a AMD (troca automática de
/// placa) e cada frase seguinte custava 1,1–1,2 s a mais para religar e restaurar o modelo
/// (medido 23/10/2026). Funciona como os jogos: um contexto OpenGL sem "renderizadores fora de
/// linha" obriga o sistema a usar a placa dedicada até ele ser fechado.
pub struct PlacaLigada(#[allow(dead_code)] *mut c_void);
unsafe impl Send for PlacaLigada {}
unsafe impl Sync for PlacaLigada {}

#[cfg(target_os = "macos")]
#[link(name = "OpenGL", kind = "framework")]
unsafe extern "C" {
    fn CGLChoosePixelFormat(attribs: *const c_int, pix: *mut *mut c_void, npix: *mut c_int) -> c_int;
    fn CGLCreateContext(pix: *mut c_void, share: *mut c_void, ctx: *mut *mut c_void) -> c_int;
    fn CGLDestroyPixelFormat(pix: *mut c_void) -> c_int;
    fn CGLDestroyContext(ctx: *mut c_void) -> c_int;
}

impl PlacaLigada {
    pub fn pedir() -> Option<Self> {
        #[cfg(target_os = "macos")]
        unsafe {
            let attrs: [c_int; 1] = [0];
            let (mut pix, mut n, mut ctx) = (std::ptr::null_mut(), 0, std::ptr::null_mut());
            if CGLChoosePixelFormat(attrs.as_ptr(), &mut pix, &mut n) != 0 || pix.is_null() {
                return None;
            }
            let ok = CGLCreateContext(pix, std::ptr::null_mut(), &mut ctx) == 0 && !ctx.is_null();
            CGLDestroyPixelFormat(pix);
            return ok.then_some(Self(ctx));
        }
        #[allow(unreachable_code)]
        None
    }
}

impl Drop for PlacaLigada {
    fn drop(&mut self) {
        #[cfg(target_os = "macos")]
        unsafe {
            CGLDestroyContext(self.0);
        }
    }
}
