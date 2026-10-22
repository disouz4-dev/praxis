//! teste-captura <programa.exe> <segundos>: grava o som do app e mostra o nível (PRAXIS_DEPURAR=1
//! mostra cada etapa). Usa o mesmo arquivo do motor (engine/src/app_audio.rs).
#[path = "../../../engine/src/app_audio.rs"]
mod app_audio;

mod vad {
    pub const CHUNK: usize = 512;
    pub const SR: usize = 16_000;
}
mod devices {
    /// sem conversão de taxa: o teste só mede o nível
    pub struct Resampler;
    impl Resampler {
        pub fn new(_de: u32, _para: u32) -> Self { Resampler }
        pub fn process(&mut self, x: &[f32]) -> Vec<f32> { x.to_vec() }
    }
}

fn main() -> anyhow::Result<()> {
    let a: Vec<String> = std::env::args().collect();
    println!("apps: {:?}", app_audio::list());
    #[cfg(windows)]
    {
        let (tx, rx) = std::sync::mpsc::channel::<Vec<f32>>();
        let stop = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
        let h = app_audio::spawn_capture(a[1].clone(), tx, stop.clone())?;
        let fim = std::time::Instant::now() + std::time::Duration::from_secs_f32(a[2].parse()?);
        let mut n = 0usize;
        let mut soma = 0f64;
        while std::time::Instant::now() < fim {
            if let Ok(c) = rx.recv_timeout(std::time::Duration::from_millis(100)) {
                n += c.len();
                soma += c.iter().map(|x| (*x as f64).powi(2)).sum::<f64>();
            }
        }
        stop.store(true, std::sync::atomic::Ordering::Relaxed);
        let _ = h.join();
        println!("amostras {n}, nível {:.4}", (soma / n.max(1) as f64).sqrt());
    }
    let _ = a;
    Ok(())
}
