//! O som de um app (o app de chamada) para o modo bilateral, escolhido numa lista:
//!   Linux    o Praxis move o som do app para a saída "Praxis Speaker" (e o devolve ao parar)
//!   Windows  grava o som do app direto (captura por processo, Windows 10 2004 ou mais novo)
//!   macOS    ainda não (lista vazia: o usuário manda a saída do app para o Praxis Speaker)

#[cfg(windows)]
use anyhow::Result;
#[cfg(any(target_os = "linux", windows))]
use std::sync::atomic::AtomicBool;
#[cfg(target_os = "linux")]
use std::sync::atomic::Ordering;
#[cfg(any(target_os = "linux", windows))]
use std::sync::Arc;

/// Um app tocando som agora. `id` identifica o app entre execuções (nome do programa).
#[derive(Debug, Clone, PartialEq, serde::Serialize)]
pub struct AudioApp {
    pub id: String,
    pub name: String,
}

/// Os apps que estão tocando som agora (sem o próprio Praxis), um por programa.
pub fn list() -> Vec<AudioApp> {
    let mut apps = imp::list();
    apps.retain(|a| !a.id.to_lowercase().starts_with("praxis"));
    let mut vistos = std::collections::HashSet::new();
    apps.retain(|a| vistos.insert(a.id.clone()));
    apps.sort_by_key(|a| a.name.to_lowercase());
    apps
}

#[cfg(not(any(target_os = "linux", windows)))]
mod imp {
    pub fn list() -> Vec<super::AudioApp> {
        vec![]
    }
}

// ── Linux ─────────────────────────────────────────────────────────────────────

#[cfg(target_os = "linux")]
mod imp {
    use super::AudioApp;

    pub struct SinkInput {
        pub index: u32,
        pub sink: u32,
        pub app: AudioApp,
    }

    fn pactl(args: &[&str]) -> Option<String> {
        let out = std::process::Command::new("pactl").env("LC_ALL", "C").args(args).output().ok()?;
        out.status.success().then(|| String::from_utf8_lossy(&out.stdout).to_string())
    }

    /// `pactl list sink-inputs` (em inglês, para o texto não mudar com o idioma do sistema)
    pub fn sink_inputs() -> Vec<SinkInput> {
        let Some(txt) = pactl(&["list", "sink-inputs"]) else { return vec![] };
        let mut v = vec![];
        let (mut index, mut sink, mut name, mut bin): (Option<u32>, u32, String, String) = (None, 0, String::new(), String::new());
        let fecha = |index: Option<u32>, sink: u32, name: &str, bin: &str, v: &mut Vec<SinkInput>| {
            if let Some(i) = index {
                let id = if bin.is_empty() { name.to_string() } else { bin.to_string() };
                let nome = if name.is_empty() { bin.to_string() } else { name.to_string() };
                if !id.is_empty() {
                    v.push(SinkInput { index: i, sink, app: AudioApp { id, name: nome } });
                }
            }
        };
        let valor = |l: &str| l.split_once(" = ").map(|(_, x)| x.trim().trim_matches('"').to_string()).unwrap_or_default();
        for l in txt.lines() {
            let t = l.trim();
            if let Some(n) = t.strip_prefix("Sink Input #") {
                fecha(index, sink, &name, &bin, &mut v);
                (index, sink, name, bin) = (n.trim().parse().ok(), 0, String::new(), String::new());
            } else if let Some(s) = t.strip_prefix("Sink: ") {
                sink = s.trim().parse().unwrap_or(0);
            } else if t.starts_with("application.name = ") {
                name = valor(t);
            } else if t.starts_with("application.process.binary = ") {
                bin = valor(t);
            }
        }
        fecha(index, sink, &name, &bin, &mut v);
        v
    }

    pub fn list() -> Vec<AudioApp> {
        sink_inputs().into_iter().map(|s| s.app).collect()
    }

    /// Número da saída `name` (ex.: Praxis_In).
    pub fn sink_index(name: &str) -> Option<u32> {
        pactl(&["list", "short", "sinks"])?.lines().find_map(|l| {
            let mut c = l.split('\t');
            let i = c.next()?.parse().ok()?;
            (c.next()? == name).then_some(i)
        })
    }

    pub fn move_to(input: u32, sink: &str) -> bool {
        pactl(&["move-sink-input", &input.to_string(), sink]).is_some()
    }
}

/// Linux: enquanto existir, manda todo som do app escolhido para a saída `sink` (inclusive
/// os que o app abrir depois, como o som de uma chamada que começa) e, ao acabar, devolve
/// esse som à saída padrão do sistema.
#[cfg(target_os = "linux")]
#[derive(Debug)]
pub struct Router {
    stop: Arc<AtomicBool>,
    handle: Option<std::thread::JoinHandle<()>>,
}

#[cfg(target_os = "linux")]
impl Router {
    pub fn start(app_id: String, sink: &str) -> Self {
        let stop = Arc::new(AtomicBool::new(false));
        let (st, sink) = (stop.clone(), sink.to_string());
        let handle = std::thread::spawn(move || {
            let mut movidos = std::collections::HashSet::new();
            while !st.load(Ordering::Relaxed) {
                if let Some(alvo) = imp::sink_index(&sink) {
                    for si in imp::sink_inputs() {
                        if (si.app.id == app_id || si.app.name == app_id) && si.sink != alvo && imp::move_to(si.index, &sink) {
                            movidos.insert(si.index);
                        }
                    }
                }
                for _ in 0..7 {
                    if st.load(Ordering::Relaxed) {
                        break;
                    }
                    std::thread::sleep(std::time::Duration::from_millis(100));
                }
            }
            let existem: std::collections::HashSet<u32> = imp::sink_inputs().iter().map(|s| s.index).collect();
            for i in movidos.intersection(&existem) {
                imp::move_to(*i, "@DEFAULT_SINK@");
            }
        });
        Self { stop, handle: Some(handle) }
    }
}

#[cfg(target_os = "linux")]
impl Drop for Router {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Relaxed);
        if let Some(h) = self.handle.take() {
            let _ = h.join();
        }
    }
}

// ── Windows ───────────────────────────────────────────────────────────────────

#[cfg(windows)]
mod imp {
    use super::AudioApp;
    use windows::core::{implement, Interface, Ref, HRESULT, PWSTR};
    use windows::Win32::Foundation::{CloseHandle, WAIT_OBJECT_0};
    use windows::Win32::Media::Audio::*;
    use windows::Win32::System::Com::StructuredStorage::PROPVARIANT;
    use windows::Win32::System::Com::{CoCreateInstance, CoInitializeEx, BLOB, CLSCTX_ALL, COINIT_MULTITHREADED};
    use windows::Win32::System::Diagnostics::ToolHelp::*;
    use windows::Win32::System::Threading::*;
    use windows::Win32::System::Variant::VT_BLOB;

    fn exe_name(pid: u32) -> Option<String> {
        unsafe {
            let h = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, false, pid).ok()?;
            let mut buf = [0u16; 1024];
            let mut n = buf.len() as u32;
            let r = QueryFullProcessImageNameW(h, PROCESS_NAME_WIN32, PWSTR(buf.as_mut_ptr()), &mut n);
            let _ = CloseHandle(h);
            r.ok()?;
            let full = String::from_utf16_lossy(&buf[..n as usize]);
            full.rsplit('\\').next().map(|s| s.to_string())
        }
    }

    /// Sessões de som ativas em todas as saídas: (processo, programa)
    fn sessions() -> Vec<(u32, String)> {
        let mut v = vec![];
        unsafe {
            let _ = CoInitializeEx(None, COINIT_MULTITHREADED);
            let en: windows::core::Result<IMMDeviceEnumerator> = CoCreateInstance(&MMDeviceEnumerator, None, CLSCTX_ALL);
            let Ok(en) = en else { return v };
            let Ok(col) = en.EnumAudioEndpoints(eRender, DEVICE_STATE_ACTIVE) else { return v };
            for d in 0..col.GetCount().unwrap_or(0) {
                let Ok(dev) = col.Item(d) else { continue };
                let Ok(mgr) = dev.Activate::<IAudioSessionManager2>(CLSCTX_ALL, None) else { continue };
                let Ok(se) = mgr.GetSessionEnumerator() else { continue };
                for i in 0..se.GetCount().unwrap_or(0) {
                    let Ok(c) = se.GetSession(i) else { continue };
                    let Ok(c2) = c.cast::<IAudioSessionControl2>() else { continue };
                    let pid = c2.GetProcessId().unwrap_or(0);
                    if pid == 0 {
                        continue; // sons do sistema
                    }
                    if let Some(exe) = exe_name(pid) {
                        v.push((pid, exe));
                    }
                }
            }
        }
        v
    }

    /// Muda o volume do app `exe` no mixer do Windows (0 a 1). Devolve quantas sessões mudou.
    pub fn set_volume(exe: &str, v: f32) -> usize {
        let mut n = 0;
        unsafe {
            let _ = CoInitializeEx(None, COINIT_MULTITHREADED);
            let en: windows::core::Result<IMMDeviceEnumerator> = CoCreateInstance(&MMDeviceEnumerator, None, CLSCTX_ALL);
            let Ok(en) = en else { return 0 };
            let Ok(col) = en.EnumAudioEndpoints(eRender, DEVICE_STATE_ACTIVE) else { return 0 };
            for d in 0..col.GetCount().unwrap_or(0) {
                let Ok(dev) = col.Item(d) else { continue };
                let Ok(mgr) = dev.Activate::<IAudioSessionManager2>(CLSCTX_ALL, None) else { continue };
                let Ok(se) = mgr.GetSessionEnumerator() else { continue };
                for i in 0..se.GetCount().unwrap_or(0) {
                    let Ok(c) = se.GetSession(i) else { continue };
                    let Ok(c2) = c.cast::<IAudioSessionControl2>() else { continue };
                    let pid = c2.GetProcessId().unwrap_or(0);
                    if exe_name(pid).is_some_and(|e| e.eq_ignore_ascii_case(exe)) {
                        if let Ok(vol) = c.cast::<ISimpleAudioVolume>() {
                            if vol.SetMasterVolume(v.clamp(0.0, 1.0), std::ptr::null()).is_ok() {
                                n += 1;
                            }
                        }
                    }
                }
            }
        }
        n
    }

    pub fn list() -> Vec<AudioApp> {
        sessions().into_iter().map(|(_, exe)| {
            let name = exe.strip_suffix(".exe").or_else(|| exe.strip_suffix(".EXE")).unwrap_or(&exe).to_string();
            AudioApp { id: exe, name }
        }).collect()
    }

    /// O processo "raiz" do programa `exe` (navegadores tocam o som num processo filho; a
    /// captura inclui a árvore inteira a partir da raiz).
    pub fn root_pid(exe: &str) -> Option<u32> {
        let mut procs: Vec<(u32, u32, String)> = vec![];
        unsafe {
            let snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0).ok()?;
            let mut e = PROCESSENTRY32W { dwSize: std::mem::size_of::<PROCESSENTRY32W>() as u32, ..Default::default() };
            if Process32FirstW(snap, &mut e).is_ok() {
                loop {
                    let n = e.szExeFile.iter().position(|&c| c == 0).unwrap_or(e.szExeFile.len());
                    procs.push((e.th32ProcessID, e.th32ParentProcessID, String::from_utf16_lossy(&e.szExeFile[..n])));
                    if Process32NextW(snap, &mut e).is_err() {
                        break;
                    }
                }
            }
            let _ = CloseHandle(snap);
        }
        let mesmo = |n: &str| n.eq_ignore_ascii_case(exe);
        // de preferência um processo que está tocando som agora, subindo até a raiz
        let tocando: Vec<u32> = sessions().into_iter().filter(|(_, e)| mesmo(e)).map(|(p, _)| p).collect();
        let inicio = tocando.first().copied().or_else(|| procs.iter().find(|p| mesmo(&p.2)).map(|p| p.0))?;
        let mut pid = inicio;
        while let Some(pai) = procs.iter().find(|p| p.0 == pid).map(|p| p.1) {
            match procs.iter().find(|p| p.0 == pai) {
                Some(p) if mesmo(&p.2) && p.0 != pid => pid = p.0,
                _ => break,
            }
        }
        Some(pid)
    }

    /// marca de progresso (PRAXIS_DEPURAR=1)
    fn passo(p: &str) {
        if std::env::var_os("PRAXIS_DEPURAR").is_some() {
            eprintln!("captura: {p}");
        }
    }

    #[implement(IActivateAudioInterfaceCompletionHandler)]
    struct Pronto(std::sync::mpsc::Sender<()>);

    impl IActivateAudioInterfaceCompletionHandler_Impl for Pronto_Impl {
        fn ActivateCompleted(&self, _op: Ref<IActivateAudioInterfaceAsyncOperation>) -> windows::core::Result<()> {
            let _ = self.0.send(());
            Ok(())
        }
    }

    /// Grava o som do processo `pid` (e dos filhos): estéreo, 16 bits, 44,1 kHz. `push` recebe
    /// blocos mono f32 a 44,1 kHz até `stop`.
    pub fn capture(pid: u32, stop: &std::sync::atomic::AtomicBool, ready: impl FnOnce(anyhow::Result<()>),
                   mut push: impl FnMut(Vec<f32>)) {
        let abrir = || -> anyhow::Result<(IAudioClient, IAudioCaptureClient, windows::Win32::Foundation::HANDLE)> {
            unsafe {
                let _ = CoInitializeEx(None, COINIT_MULTITHREADED);
                passo("com");
                let mut params = AUDIOCLIENT_ACTIVATION_PARAMS {
                    ActivationType: AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK,
                    Anonymous: AUDIOCLIENT_ACTIVATION_PARAMS_0 {
                        ProcessLoopbackParams: AUDIOCLIENT_PROCESS_LOOPBACK_PARAMS {
                            TargetProcessId: pid,
                            ProcessLoopbackMode: PROCESS_LOOPBACK_MODE_INCLUDE_TARGET_PROCESS_TREE,
                        },
                    },
                };
                let mut pv = PROPVARIANT::default();
                (*pv.Anonymous.Anonymous).vt = VT_BLOB;
                (*pv.Anonymous.Anonymous).Anonymous.blob = BLOB {
                    cbSize: std::mem::size_of::<AUDIOCLIENT_ACTIVATION_PARAMS>() as u32,
                    pBlobData: &mut params as *mut _ as *mut u8,
                };
                let (tx, rx) = std::sync::mpsc::channel();
                let handler: IActivateAudioInterfaceCompletionHandler = Pronto(tx).into();
                passo("ativar");
                let op = ActivateAudioInterfaceAsync(VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK, &IAudioClient::IID, Some(&pv), &handler)?;
                rx.recv_timeout(std::time::Duration::from_secs(5))
                    .map_err(|_| anyhow::anyhow!("o Windows não respondeu ao pedido de gravar o som do app"))?;
                passo("ativado");
                let mut hr = HRESULT(0);
                let mut unk = None;
                op.GetActivateResult(&mut hr, &mut unk)?;
                hr.ok()?;
                passo("resultado");
                let client: IAudioClient = unk.ok_or_else(|| anyhow::anyhow!("captura do app indisponível"))?.cast()?;
                let fmt = WAVEFORMATEX {
                    wFormatTag: WAVE_FORMAT_PCM as u16, nChannels: 2, nSamplesPerSec: 44_100,
                    nAvgBytesPerSec: 44_100 * 4, nBlockAlign: 4, wBitsPerSample: 16, cbSize: 0,
                };
                passo("iniciar");
                client.Initialize(AUDCLNT_SHAREMODE_SHARED,
                    AUDCLNT_STREAMFLAGS_LOOPBACK | AUDCLNT_STREAMFLAGS_EVENTCALLBACK | AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM,
                    0, 0, &fmt, None)?;   // como o exemplo da Microsoft: o Windows escolhe o buffer
                let ev = CreateEventW(None, false, false, None)?;
                client.SetEventHandle(ev)?;
                let cap: IAudioCaptureClient = client.GetService()?;
                passo("start");
                client.Start()?;
                Ok((client, cap, ev))
            }
        };
        let (client, cap, ev) = match abrir() {
            Ok(x) => {
                ready(Ok(()));
                x
            }
            Err(e) => return ready(Err(e)),
        };
        unsafe {
            while !stop.load(std::sync::atomic::Ordering::Relaxed) {
                if WaitForSingleObject(ev, 200) != WAIT_OBJECT_0 {
                    continue;
                }
                while let Ok(n) = cap.GetNextPacketSize() {
                    if n == 0 {
                        break;
                    }
                    let (mut data, mut frames, mut flags) = (std::ptr::null_mut(), 0u32, 0u32);
                    passo("pacote pronto");
                    if cap.GetBuffer(&mut data, &mut frames, &mut flags, None, None).is_err() {
                        break;
                    }
                    let mono: Vec<f32> = if flags & (AUDCLNT_BUFFERFLAGS_SILENT.0 as u32) != 0 || data.is_null() {
                        vec![0.0; frames as usize]
                    } else {
                        let s = std::slice::from_raw_parts(data as *const i16, frames as usize * 2);
                        s.chunks(2).map(|f| (f[0] as f32 + f[1] as f32) / (2.0 * 32768.0)).collect()
                    };
                    let _ = cap.ReleaseBuffer(frames);
                    if std::env::var_os("PRAXIS_DEPURAR").is_some() { eprintln!("pacote {frames} flags {flags}"); }
                    push(mono);
                }
            }
            let _ = client.Stop();
            let _ = CloseHandle(ev);
        }
    }
}

/// Windows: volume do app no mixer do sistema (0 a 1); devolve quantas sessões mudaram.
#[cfg(windows)]
pub fn set_app_volume(app_id: &str, v: f32) -> usize {
    imp::set_volume(app_id, v)
}

/// Windows: grava o som do app `app_id` (ex.: "Discord.exe") em blocos de 32 ms, mono, 16 kHz.
#[cfg(windows)]
pub fn spawn_capture(app_id: String, tx: std::sync::mpsc::Sender<Vec<f32>>, stop: Arc<AtomicBool>) -> Result<std::thread::JoinHandle<()>> {
    use crate::vad::{CHUNK, SR};
    let pid = imp::root_pid(&app_id).ok_or_else(|| anyhow::anyhow!("o app {app_id} não está aberto: abra a chamada e tente de novo"))?;
    let (rtx, rrx) = std::sync::mpsc::channel::<Result<()>>();
    let h = std::thread::spawn(move || {
        let mut rs = crate::devices::Resampler::new(44_100, SR as u32);
        let mut buf: Vec<f32> = vec![];
        imp::capture(pid, &stop, |r| { let _ = rtx.send(r); }, |mono| {
            buf.extend(rs.process(&mono));
            while buf.len() >= CHUNK {
                let _ = tx.send(buf.drain(..CHUNK).collect());
            }
        });
    });
    rrx.recv().map_err(|_| anyhow::anyhow!("a gravação do app parou"))??;
    Ok(h)
}

#[cfg(all(test, target_os = "linux"))]
mod tests {
    #[test]
    fn lista_nao_quebra_sem_pactl_ou_sem_som() {
        // num computador sem som tocando a lista vem vazia, nunca com erro
        let _ = super::list();
    }
}
