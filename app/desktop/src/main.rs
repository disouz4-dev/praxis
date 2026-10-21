//! Praxis — aplicativo de janela (Tauri). Toda a lógica está no motor (praxis-engine);
//! aqui ficam só os comandos que a janela chama e o repasse dos eventos do motor.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::PathBuf;
use std::sync::Mutex;

use praxis_engine::devices;
use praxis_engine::models::ModelStore;
use praxis_engine::session::{self, Session, SessionConfig, SessionEvent};
use serde_json::{json, Value};
use tauri::{Emitter, Manager, State};

#[derive(Default)]
struct App {
    session: Mutex<Option<Session>>,
    gpu: Mutex<Option<bool>>,
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
    })
}

#[tauri::command]
fn salvar_config(config: Value) -> Result<(), String> {
    let p = config_path();
    std::fs::create_dir_all(p.parent().unwrap()).map_err(|e| e.to_string())?;
    let tmp = p.with_extension("json.tmp");
    std::fs::write(&tmp, serde_json::to_string_pretty(&config).unwrap()).map_err(|e| e.to_string())?;
    std::fs::rename(tmp, p).map_err(|e| e.to_string())
}

#[tauri::command]
fn dispositivos() -> Value {
    json!({"entradas": devices::list_inputs(), "saidas": devices::list_outputs()})
}

/// Liga o Praxis. Baixa o que faltar (com progresso) e carrega os modelos numa tarefa à
/// parte; a janela recebe tudo pelo evento "praxis".
#[tauri::command]
fn iniciar(handle: tauri::AppHandle, config: SessionConfig) -> Result<(), String> {
    if handle.state::<App>().session.lock().unwrap().is_some() {
        return Err("o Praxis já está traduzindo".into());
    }
    std::thread::spawn(move || {
        let (tx, rx) = std::sync::mpsc::channel::<SessionEvent>();
        let h2 = handle.clone();
        let fwd = std::thread::spawn(move || {
            while let Ok(e) = rx.recv() {
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
    tauri::Builder::default()
        .manage(App::default())
        .invoke_handler(tauri::generate_handler![estado_inicial, salvar_config, dispositivos, iniciar, parar])
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
