//! Praxis — aplicativo de janela (Tauri). Toda a lógica está no motor (praxis-engine);
//! aqui ficam só os comandos que a janela chama e o repasse dos eventos do motor.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::PathBuf;
use std::sync::Mutex;

mod erros;

use praxis_engine::devices;
use praxis_engine::models::ModelStore;
use praxis_engine::session::{self, Session, SessionConfig, SessionEvent};
use serde_json::{json, Value};
use tauri::{Emitter, Manager, State};

#[derive(Default)]
struct App {
    session: Mutex<Option<Session>>,
    gpu: Mutex<Option<bool>>,
    /// teste do microfone em andamento (o sinal de parar)
    teste_mic: Mutex<Option<std::sync::Arc<std::sync::atomic::AtomicBool>>>,
    /// gravação da voz do usuário em andamento: (sinal de parar, amostras a 16 kHz)
    gravacao: Mutex<Option<(std::sync::Arc<std::sync::atomic::AtomicBool>, std::sync::Arc<Mutex<Vec<f32>>>)>>,
    /// clonagem da voz em andamento (o sinal de cancelar)
    clonagem: Mutex<Option<std::sync::Arc<std::sync::atomic::AtomicBool>>>,
}

/// A gravação da voz do usuário (obrigatória: amostra da voz clonada).
fn voz_path() -> PathBuf {
    dirs::data_dir().unwrap_or_else(std::env::temp_dir).join("Praxis").join("voz").join("minha_voz.wav")
}

/// Segundos com fala (blocos de 32 ms acima do silêncio) e tom médio de uma gravação.
fn medir_voz(x: &[f32]) -> (f32, Option<f32>) {
    let fala = x.chunks(512).filter(|b| (b.iter().map(|v| v * v).sum::<f32>() / b.len() as f32).sqrt() > 0.012).count();
    (fala as f32 * 512.0 / 16_000.0, praxis_engine::audio::tom_medio(x, 16_000))
}

/// A voz clonada (voice.bin do Supertonic) e o registro de qual gravação a gerou.
fn clone_path() -> PathBuf {
    voz_path().with_file_name("minha_voz_clonada.bin")
}
fn clone_info_path() -> PathBuf {
    voz_path().with_file_name("minha_voz_clonada.json")
}

/// O OmniVoice (clone na placa de vídeo) está instalado? Com ele, a gravação já é o clone: não
/// há ajuste a esperar.
fn omni_pronto() -> bool {
    praxis_engine::omni::caminho_biblioteca().exists()
        && ModelStore::default_location().is_ok_and(|s| {
            let d = s.omnivoice_dir();
            d.join(praxis_engine::models::OMNI_MODELO).exists() && d.join(praxis_engine::models::OMNI_CODEC).exists()
        })
}

/// A voz clonada existe e foi feita a partir da gravação atual?
fn clone_em_dia() -> Option<praxis_engine::clone::Clone> {
    let info: praxis_engine::clone::Clone = serde_json::from_str(&std::fs::read_to_string(clone_info_path()).ok()?).ok()?;
    let sha = praxis_engine::models::sha256_arquivo(&voz_path()).ok()?;
    (clone_path().exists() && info.gravacao_sha256 == sha).then_some(info)
}

fn estado_da_voz() -> Value {
    let p = voz_path();
    match praxis_engine::audio::read_wav_16k_mono(&p) {
        Ok(x) => {
            let (fala, tom) = medir_voz(&x);
            let clone = clone_em_dia();
            // só vale como voz gravada com 10 s de fala (a mesma regra de quando grava)
            let omni = omni_pronto();
            json!({"existe": fala >= 10.0, "segundos": (fala * 10.0).round() / 10.0, "tom": tom, "caminho": p,
                   "clonada": omni || clone.is_some(), "omnivoice": omni, "semelhanca": clone.map(|c| c.semelhanca)})
        }
        Err(_) => json!({"existe": false, "clonada": false}),
    }
}

/// Clona a voz da gravação atual em segundo plano (evento "clonagem": fração, texto, fim, erro).
/// Uma clonagem anterior em andamento é cancelada.
fn iniciar_clonagem(handle: tauri::AppHandle) {
    // com o OmniVoice a gravação já é o clone; o ajuste no processador só roubaria tempo
    if omni_pronto() {
        let _ = handle.emit("clonagem", json!({"fim": true, "omnivoice": true}));
        return;
    }
    let parar = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    if let Some(antiga) = handle.state::<App>().clonagem.lock().unwrap().replace(parar.clone()) {
        antiga.store(true, std::sync::atomic::Ordering::Relaxed);
    }
    std::thread::spawn(move || {
        let emitir = |v: Value| { let _ = handle.emit("clonagem", v); };
        let r = (|| -> anyhow::Result<praxis_engine::clone::Clone> {
            let store = ModelStore::default_location()?;
            let baixando = |o: &str, a: u64, t: u64| {
                let f = if t > 0 { a as f32 / t as f32 } else { 0.0 };
                emitir(json!({"fracao": 0.0, "texto": format!("Baixando {o}… {:.0}%", f * 100.0)}));
            };
            let pacote = store.ensure_supertonic(&baixando)?;
            let medidor = store.ensure_speaker_model(&baixando)?;
            let gravacao = praxis_engine::audio::read_wav_16k_mono(&voz_path())?;
            let sha = praxis_engine::models::sha256_arquivo(&voz_path())?;
            let threads = std::thread::available_parallelism().map(|n| n.get().min(4)).unwrap_or(4) as i32;
            let mut c = praxis_engine::clone::clonar(&gravacao, &pacote, &medidor, &clone_path(), praxis_engine::clone::RODADAS,
                threads, &|f, t| emitir(json!({"fracao": f, "texto": t})), &parar)?;
            c.gravacao_sha256 = sha;
            std::fs::write(clone_info_path(), serde_json::to_string_pretty(&c)?)?;
            Ok(c)
        })();
        match r {
            Ok(c) => emitir(json!({"fim": true, "semelhanca": c.semelhanca, "pronta": c.semelhanca_pronta, "segundos": c.segundos})),
            Err(e) if parar.load(std::sync::atomic::Ordering::Relaxed) => { let _ = e; }
            Err(e) => {
                erros::registrar("clonagem", &format!("{e:#}"));
                emitir(json!({"erro": format!("{e:#}")}));
            }
        }
        let st = handle.state::<App>();
        let mut g = st.clonagem.lock().unwrap();
        if g.as_ref().is_some_and(|p| std::sync::Arc::ptr_eq(p, &parar)) {
            *g = None;
        }
    });
}

/// Clona (ou refaz) a voz a partir da gravação atual.
#[tauri::command]
fn clonar_voz(handle: tauri::AppHandle) -> Result<(), String> {
    if !estado_da_voz()["existe"].as_bool().unwrap_or(false) {
        return Err("grave a sua voz antes de clonar".into());
    }
    iniciar_clonagem(handle);
    Ok(())
}

fn config_path() -> PathBuf {
    dirs::config_dir().unwrap_or_else(std::env::temp_dir).join("Praxis").join("praxis.json")
}

/// Idioma do sistema ("pt-BR" → "pt"): a interface e "você fala" herdam dele na 1ª vez.
fn system_language() -> String {
    sys_locale::get_locale().unwrap_or_else(|| "en".into()).split(['-', '_']).next().unwrap_or("en").to_lowercase()
}

#[tauri::command]
fn estado_inicial(app: State<App>) -> Value {
    let gpu = *app.gpu.lock().unwrap().get_or_insert_with(session::has_nvidia_gpu);
    let idiomas: Vec<Value> = ["pt", "en", "es", "fr", "de", "it", "ja", "zh", "ko", "ru", "ar", "hi", "nl", "pl", "uk", "tr"]
        .iter()
        .map(|l| {
            let (ok, why) = session::language_allowed(l, gpu);
            json!({"codigo": l, "liberado": ok, "motivo": why,
                   "tem_voz": praxis_engine::models::voice_choice(l, gpu).is_some(),
                   // diagnóstico: o reconhecedor escolhido para este idioma e o erro medido
                   "modelo": session::asr_model_for(l, gpu, "auto"),
                   "erro": session::measured_error(l, gpu)})
        })
        .collect();
    let salva: Value = std::fs::read_to_string(config_path()).ok().and_then(|s| serde_json::from_str(&s).ok()).unwrap_or(Value::Null);
    json!({
        "placa_de_video": gpu,
        "entradas": devices::list_inputs(),
        "saidas": devices::list_outputs(),
        "idiomas": idiomas,
        "idioma_do_sistema": system_language(),
        "config": salva,
        "rodando": app.session.lock().unwrap().is_some(),
        "sistema": std::env::consts::OS,
        "versao": env!("CARGO_PKG_VERSION"),
        "voz": estado_da_voz(),
        "apps": praxis_engine::app_audio::list(),
    })
}

/// Apps tocando som agora (bilateral: de qual app vem a outra pessoa).
#[tauri::command]
fn apps_com_som() -> Value {
    json!(praxis_engine::app_audio::list())
}

#[tauri::command]
fn salvar_config(config: Value) -> Result<(), String> {
    let p = config_path();
    std::fs::create_dir_all(p.parent().unwrap()).map_err(|e| e.to_string())?;
    let tmp = p.with_extension("json.tmp");
    std::fs::write(&tmp, serde_json::to_string_pretty(&config).unwrap()).map_err(|e| e.to_string())?;
    std::fs::rename(tmp, p).map_err(|e| e.to_string())
}

/// Verificação de qualidade automática: com PRAXIS_QA_INICIAR=1 a janela começa a traduzir
/// sozinha ao abrir (o mesmo caminho do botão "Iniciar").
#[tauri::command]
fn modo_qa() -> bool {
    std::env::var("PRAXIS_QA_INICIAR").map(|v| v == "1").unwrap_or(false)
}

/// Atualizador do .deb, quando instalado (Linux): pede a senha e chama o apt.
const LINUX_UPDATER: &str = "/opt/praxis/praxis-atualizar";

/// Há versão nova? `pode_atualizar`: este sistema sabe se atualizar sozinho (Windows; Linux
/// instalado pelo .deb); nos outros a janela manda para a página de versões. `erro`: não deu
/// para perguntar ao GitHub (sem internet) — a janela não pode dizer "está atualizado".
#[tauri::command]
async fn verificar_atualizacao() -> Value {
    let atual = env!("CARGO_PKG_VERSION");
    let pode = cfg!(windows) || (cfg!(target_os = "linux") && std::path::Path::new(LINUX_UPDATER).exists());
    match tauri::async_runtime::spawn_blocking(praxis_engine::update::latest_version).await {
        Ok(Ok(n)) => json!({"atual": atual, "nova": praxis_engine::update::is_newer(&n, atual).then_some(n), "pode_atualizar": pode}),
        Ok(Err(e)) => json!({"atual": atual, "nova": null, "pode_atualizar": pode, "erro": e.to_string()}),
        Err(e) => json!({"atual": atual, "nova": null, "pode_atualizar": pode, "erro": e.to_string()}),
    }
}

/// Abre no navegador um endereço do próprio Praxis (página, código, versões).
#[tauri::command]
fn abrir_link(url: String) -> Result<(), String> {
    let ok = ["https://disouz4-dev.github.io/praxis", "https://github.com/disouz4-dev/praxis"].iter().any(|p| url.starts_with(p));
    if !ok {
        return Err("endereço não permitido".into());
    }
    erros::abrir_navegador(&url)
}

/// Instala a versão nova e reabre o Praxis. Linux: pede a senha e chama o apt. Windows: baixa
/// o instalador; um PowerShell à parte espera o Praxis fechar, instala sem perguntas e reabre.
#[tauri::command]
async fn atualizar(app: tauri::AppHandle) -> Result<(), String> {
    if cfg!(windows) {
        let setup = tauri::async_runtime::spawn_blocking(|| -> anyhow::Result<std::path::PathBuf> {
            let v = praxis_engine::update::latest_version()?;
            praxis_engine::update::download_windows_setup(&v)
        })
        .await
        .map_err(|e| e.to_string())?
        .map_err(|e| format!("não foi possível baixar a versão nova: {e}"))?;
        let exe = std::env::current_exe().map_err(|e| e.to_string())?;
        let ps = format!(
            "Wait-Process -Id {} -ErrorAction SilentlyContinue; Start-Process -Wait -FilePath '{}' -ArgumentList '/S'; Start-Process -FilePath '{}'",
            std::process::id(), setup.display(), exe.display());
        let mut cmd = std::process::Command::new("powershell");
        cmd.args(["-NoProfile", "-WindowStyle", "Hidden", "-Command", &ps]);
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            cmd.creation_flags(0x0000_0008 | 0x0800_0000);   // DETACHED_PROCESS | CREATE_NO_WINDOW
        }
        cmd.spawn().map_err(|e| format!("não foi possível iniciar a atualização: {e}"))?;
        app.exit(0);
        return Ok(());
    }
    let ok = tauri::async_runtime::spawn_blocking(|| std::process::Command::new("pkexec").arg(LINUX_UPDATER).status())
        .await
        .map_err(|e| e.to_string())?
        .map_err(|e| format!("não foi possível pedir a senha: {e}"))?;
    if !ok.success() {
        return Err("a atualização não terminou (senha cancelada ou sem internet)".into());
    }
    app.restart();
}

#[tauri::command]
fn dispositivos() -> Value {
    json!({"entradas": devices::list_inputs(), "saidas": devices::list_outputs()})
}

/// Liga o Praxis. Baixa o que faltar (com progresso) e carrega os modelos numa tarefa à
/// parte; a janela recebe tudo pelo evento "praxis".
/// Teste do microfone antes de traduzir: grava o microfone escolhido e manda o volume para a
/// janela ("nivel_mic", de 0 a 1, ~12 vezes por segundo) até parar ou passar 2 minutos.
#[tauri::command]
fn testar_microfone(handle: tauri::AppHandle, nome: Option<String>) -> Result<(), String> {
    parar_teste_microfone(handle.clone());
    if handle.state::<App>().session.lock().unwrap().is_some() {
        return Err("o Praxis já está traduzindo".into());
    }
    let stop = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    let (tx, rx) = std::sync::mpsc::channel::<Vec<f32>>();
    devices::spawn_capture(nome.filter(|n| !n.is_empty()), tx, stop.clone()).map_err(|e| format!("{e:#}"))?;
    *handle.state::<App>().teste_mic.lock().unwrap() = Some(stop.clone());
    std::thread::spawn(move || {
        let inicio = std::time::Instant::now();
        let mut ultimo = std::time::Instant::now();
        let mut pico = 0f32;
        while let Ok(bloco) = rx.recv() {
            let rms = (bloco.iter().map(|x| x * x).sum::<f32>() / bloco.len().max(1) as f32).sqrt();
            pico = pico.max(rms);
            if ultimo.elapsed().as_millis() >= 80 {
                // escala de voz: fala normal (~0,05) enche boa parte da barra
                let _ = handle.emit("nivel_mic", json!({"nivel": (pico * 8.0).min(1.0)}));
                pico = 0.0;
                ultimo = std::time::Instant::now();
            }
            if inicio.elapsed().as_secs() > 120 {
                stop.store(true, std::sync::atomic::Ordering::Relaxed);
            }
        }
        let _ = handle.emit("nivel_mic", json!({"nivel": 0.0, "parou": true}));
    });
    Ok(())
}

/// Painel lateral da tradução ao vivo (como na versão antiga): ao começar a traduzir a janela
/// se alarga para a direita e mostra a conversa ao lado das configurações; ao fechar o painel
/// volta à largura normal. Se passar da borda da tela, a janela é puxada para dentro.
#[tauri::command]
fn painel_lateral(handle: tauri::AppHandle, aberto: bool) -> Result<(), String> {
    const NORMAL: f64 = 560.0;
    const LARGA: f64 = 1100.0;
    let w = handle.get_webview_window("main").ok_or("janela principal não encontrada")?;
    let esc = w.scale_factor().unwrap_or(1.0);
    let tam = w.inner_size().map_err(|e| e.to_string())?.to_logical::<f64>(esc);
    let largura = if aberto { tam.width.max(LARGA) } else if tam.width > NORMAL + 200.0 { NORMAL } else { tam.width };
    w.set_size(tauri::LogicalSize::new(largura, tam.height)).map_err(|e| e.to_string())?;
    // cresce (ou encolhe) igual para os dois lados: o centro da janela fica no mesmo lugar,
    // sem passar das bordas da tela
    if let (Ok(Some(tela)), Ok(pos)) = (w.current_monitor(), w.outer_position()) {
        let ini_tela = tela.position().x as f64 / esc;
        let fim_tela = ini_tela + tela.size().width as f64 / esc;
        let x = pos.x as f64 / esc - (largura - tam.width) / 2.0;
        let novo_x = x.min(fim_tela - largura).max(ini_tela);
        let _ = w.set_position(tauri::LogicalPosition::new(novo_x, pos.y as f64 / esc));
    }
    Ok(())
}

/// Grava a voz do usuário (lendo o texto do tutorial): manda volume e tempo para a janela
/// ("gravacao_voz") até `parar_gravacao_voz` ou 90 segundos.
#[tauri::command]
fn gravar_voz(handle: tauri::AppHandle, nome: Option<String>) -> Result<(), String> {
    parar_teste_microfone(handle.clone());
    // um segundo clique não deixa a primeira gravação com o microfone aberto
    if let Some((antiga, _)) = handle.state::<App>().gravacao.lock().unwrap().take() {
        antiga.store(true, std::sync::atomic::Ordering::Relaxed);
    }
    let stop = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    let buf = std::sync::Arc::new(Mutex::new(Vec::<f32>::new()));
    let (tx, rx) = std::sync::mpsc::channel::<Vec<f32>>();
    devices::spawn_capture(nome.filter(|n| !n.is_empty()), tx, stop.clone()).map_err(|e| format!("{e:#}"))?;
    *handle.state::<App>().gravacao.lock().unwrap() = Some((stop.clone(), buf.clone()));
    std::thread::spawn(move || {
        let mut ultimo = std::time::Instant::now();
        let mut pico = 0f32;
        let mut limite = false;
        while let Ok(bloco) = rx.recv() {
            let rms = (bloco.iter().map(|x| x * x).sum::<f32>() / bloco.len().max(1) as f32).sqrt();
            pico = pico.max(rms);
            let total = {
                let mut b = buf.lock().unwrap();
                b.extend_from_slice(&bloco);
                b.len() as f32 / 16_000.0
            };
            if ultimo.elapsed().as_millis() >= 80 {
                let _ = handle.emit("gravacao_voz", json!({"nivel": (pico * 8.0).min(1.0), "segundos": total}));
                pico = 0.0;
                ultimo = std::time::Instant::now();
            }
            if total > 92.0 { // folga: a janela termina aos 90 s
                limite = true;
                stop.store(true, std::sync::atomic::Ordering::Relaxed);
            }
        }
        // acabou sozinha (limite de tempo ou o microfone sumiu): a janela termina a gravação.
        // Parada pelo botão ou por uma gravação nova não avisa (não pode parar a nova).
        if !limite && stop.load(std::sync::atomic::Ordering::Relaxed) {
            return;
        }
        let total = buf.lock().unwrap().len() as f32 / 16_000.0;
        let _ = handle.emit("gravacao_voz", json!({"nivel": 0.0, "segundos": total, "fim": true}));
    });
    Ok(())
}

/// Termina a gravação. Guarda só se tiver pelo menos 10 s de fala (senão a anterior continua).
#[tauri::command]
fn parar_gravacao_voz(handle: tauri::AppHandle) -> Result<Value, String> {
    let Some((stop, buf)) = handle.state::<App>().gravacao.lock().unwrap().take() else {
        return Err("nenhuma gravação em andamento".into());
    };
    stop.store(true, std::sync::atomic::Ordering::Relaxed);
    std::thread::sleep(std::time::Duration::from_millis(250));
    let x = std::mem::take(&mut *buf.lock().unwrap());
    let (fala, tom) = medir_voz(&x);
    let ok = fala >= 10.0;
    if ok {
        let p = voz_path();
        std::fs::create_dir_all(p.parent().unwrap()).map_err(|e| e.to_string())?;
        praxis_engine::audio::write_wav16(&p, &x, 16_000).map_err(|e| format!("{e:#}"))?;
        // gravação nova: o Praxis clona a voz sozinho (a anterior deixa de valer)
        iniciar_clonagem(handle.clone());
    }
    Ok(json!({"ok": ok, "fala": (fala * 10.0).round() / 10.0, "total": x.len() as f32 / 16_000.0, "tom": tom}))
}

#[tauri::command]
fn estado_voz() -> Value {
    estado_da_voz()
}

#[tauri::command]
fn parar_teste_microfone(handle: tauri::AppHandle) {
    if let Some(stop) = handle.state::<App>().teste_mic.lock().unwrap().take() {
        stop.store(true, std::sync::atomic::Ordering::Relaxed);
    }
}

#[tauri::command]
fn iniciar(handle: tauri::AppHandle, mut config: SessionConfig) -> Result<(), String> {
    parar_teste_microfone(handle.clone());
    // a voz do usuário é obrigatória (amostra da voz clonada)
    // (conferida pelo conteúdo: um arquivo estragado ou curto não serve)
    if !estado_da_voz()["segundos"].as_f64().is_some_and(|s| s >= 10.0) {
        return Err("grave a sua voz antes de começar (tutorial ou passo \"Sua voz\")".into());
    }
    // a tradução só sai na voz clonada (premissa do Praxis)
    if !omni_pronto() && clone_em_dia().is_none() {
        return Err("a sua voz ainda está sendo clonada; espere terminar (passo \"Sua voz\")".into());
    }
    config.minha_voz = Some(voz_path().to_string_lossy().to_string());
    config.voz_clonada = clone_em_dia().map(|_| clone_path().to_string_lossy().to_string());
    if handle.state::<App>().session.lock().unwrap().is_some() {
        return Err("o Praxis já está traduzindo".into());
    }
    std::thread::spawn(move || {
        let (tx, rx) = std::sync::mpsc::channel::<SessionEvent>();
        let h2 = handle.clone();
        // PRAXIS_REGISTRO=<arquivo>: guarda cada evento do motor (verificação de qualidade)
        let mut log = std::env::var_os("PRAXIS_REGISTRO").and_then(|p| std::fs::File::create(p).ok());
        let fwd = std::thread::spawn(move || {
            while let Ok(e) = rx.recv() {
                erros::registrar_evento(&serde_json::to_value(&e).unwrap_or_default());
                if let Some(f) = log.as_mut() {
                    use std::io::Write;
                    let _ = writeln!(f, "{}", serde_json::to_string(&e).unwrap_or_default());
                }
                let _ = h2.emit("praxis", &e);
            }
        });
        let result = ModelStore::default_location().and_then(|store| Session::start(config, &store, tx.clone()));
        match result {
            Ok(s) => *handle.state::<App>().session.lock().unwrap() = Some(s),
            Err(e) => {
                let _ = tx.send(SessionEvent::Error { msg: format!("{e:#}") });
                let _ = tx.send(SessionEvent::Stopped);
            }
        }
        drop(tx);
        let _ = fwd.join();
    });
    Ok(())
}

/// Monitor de erros: o relatório que vai para o GitHub (o usuário vê tudo antes).
#[tauri::command]
fn relatorio_de_erros(app: State<App>) -> String {
    let gpu = *app.gpu.lock().unwrap().get_or_insert_with(session::has_nvidia_gpu);
    let cfg: Value = std::fs::read_to_string(config_path()).ok().and_then(|s| serde_json::from_str(&s).ok()).unwrap_or(Value::Null);
    erros::relatorio(&cfg, gpu)
}

#[tauri::command]
fn abrir_relato(corpo: String) -> Result<(), String> {
    erros::abrir_relato(&corpo)
}

/// Liga ou desliga a monitoria (ouvir a própria tradução) com a tradução em andamento.
#[tauri::command]
fn definir_monitor(handle: tauri::AppHandle, ligado: bool) {
    if let Some(s) = handle.state::<App>().session.lock().unwrap().as_ref() {
        s.set_monitor(ligado);
    }
}

#[tauri::command]
fn parar(handle: tauri::AppHandle) {
    let s = handle.state::<App>().session.lock().unwrap().take();
    if let Some(s) = s {
        std::thread::spawn(move || {
            s.stop();
            let _ = handle.emit("praxis", &SessionEvent::Stopped);
        });
    }
}

fn main() {
    erros::instalar_gancho();
    tauri::Builder::default()
        .manage(App::default())
        .invoke_handler(tauri::generate_handler![estado_inicial, apps_com_som, gravar_voz, parar_gravacao_voz, estado_voz, testar_microfone, parar_teste_microfone, painel_lateral, relatorio_de_erros, abrir_relato, abrir_link, salvar_config, dispositivos, iniciar, parar, definir_monitor, clonar_voz, modo_qa, verificar_atualizacao, atualizar])
        .on_window_event(|w, e| {
            // ao fechar a janela, para o motor e remove os dispositivos virtuais
            if let tauri::WindowEvent::CloseRequested { .. } = e {
                if let Some(s) = w.state::<App>().session.lock().unwrap().take() {
                    s.stop();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("erro ao abrir o Praxis");
}
