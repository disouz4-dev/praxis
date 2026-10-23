//! praxis-hardware: mostra o que o Praxis identifica nesta máquina e o uso de cada peça.
#[path = "../../../engine/src/hardware.rs"]
mod hardware;

fn main() {
    println!("{}", serde_json::to_string_pretty(hardware::identificar()).unwrap());
    let m = hardware::Monitor::default();
    m.ler(); // a primeira leitura do processador é a base
    for _ in 0..3 {
        std::thread::sleep(std::time::Duration::from_secs(1));
        println!("{}", m.ler());
    }
}
