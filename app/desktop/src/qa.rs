//! Modo de verificação (QA): controla a janela real do Praxis nos três sistemas.
//!
//! Só existe com PRAXIS_QA_PORTA=<porta>: o Praxis escuta em 127.0.0.1 (nunca de fora do próprio
//! computador). Cada linha recebida é um trecho de JavaScript executado na janela; o resultado
//! (JSON) volta numa linha. Serve para percorrer telas, clicar, ler textos e medir, com o mesmo
//! roteiro no Linux (WebKitGTK), no Mac (WebKit) e no Windows (WebView2).

use std::collections::HashMap;
use std::io::{BufRead, BufReader, Write};
use std::sync::mpsc::{channel, Sender};
use std::sync::{Mutex, OnceLock};

use tauri::Manager;

fn pendentes() -> &'static Mutex<HashMap<u64, Sender<String>>> {
    static P: OnceLock<Mutex<HashMap<u64, Sender<String>>>> = OnceLock::new();
    P.get_or_init(|| Mutex::new(HashMap::new()))
}

/// A janela devolve o resultado de um trecho
#[tauri::command]
pub fn qa_resposta(id: u64, r: String) {
    if let Some(tx) = pendentes().lock().unwrap().remove(&id) {
        let _ = tx.send(r);
    }
}

pub fn iniciar(app: tauri::AppHandle) {
    let Some(porta) = std::env::var("PRAXIS_QA_PORTA").ok().and_then(|p| p.parse::<u16>().ok()) else { return };
    std::thread::spawn(move || {
        let Ok(l) = std::net::TcpListener::bind(("127.0.0.1", porta)) else {
            eprintln!("[qa] porta {porta} ocupada");
            return;
        };
        eprintln!("[qa] ouvindo em 127.0.0.1:{porta}");
        let mut seq = 0u64;
        for c in l.incoming().flatten() {
            let mut saida = match c.try_clone() { Ok(s) => s, Err(_) => continue };
            for linha in BufReader::new(c).lines().map_while(Result::ok) {
                seq += 1;
                let id = seq;
                let (tx, rx) = channel();
                pendentes().lock().unwrap().insert(id, tx);
                let js = format!(
                    "(async () => {{ let r; try {{ r = await (async () => {{ {linha} }})(); r = JSON.stringify(r === undefined ? null : r); }} \
                     catch (e) {{ r = JSON.stringify({{erro: String(e && e.stack || e)}}); }} \
                     window.__TAURI__.core.invoke('qa_resposta', {{ id: {id}, r }}); }})()");
                let r = match app.get_webview_window("main").map(|w| w.eval(&js)) {
                    Some(Ok(())) => rx.recv_timeout(std::time::Duration::from_secs(120)).unwrap_or_else(|_| "{\"erro\":\"sem resposta em 120 s\"}".into()),
                    _ => "{\"erro\":\"janela indisponível\"}".into(),
                };
                pendentes().lock().unwrap().remove(&id);
                if writeln!(saida, "{}", r.replace('\n', " ")).is_err() { break; }
            }
        }
    });
}
