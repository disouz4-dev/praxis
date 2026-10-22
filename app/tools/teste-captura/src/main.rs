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
        // 3º argumento: volume do app no mixer do Windows antes de gravar (0 a 1)
        if let Some(v) = a.get(3) {
            println!("volume {v}: {} sessões", app_audio::set_app_volume(&a[1], v.parse()?));
        }
        let h = app_audio::spawn_capture(a[1].clone(), tx, stop.clone())?;
        let fim = std::time::Instant::now() + std::time::Duration::from_secs_f32(a[2].parse()?);
        let mut n = 0usize;
        let mut soma = 0f64;
        let (mut janela, mut sj, mut nj) = (std::time::Instant::now(), 0f64, 0usize);
        while std::time::Instant::now() < fim {
            if let Ok(c) = rx.recv_timeout(std::time::Duration::from_millis(100)) {
                n += c.len();
                let q = c.iter().map(|x| (*x as f64).powi(2)).sum::<f64>();
                soma += q;
                sj += q;
                nj += c.len();
            }
            // nível a cada 2 s (mostra se o som volta depois que o app troca de processo)
            if janela.elapsed().as_secs_f32() >= 2.0 {
                println!("  {:>5.1}s nível {:.4} ({} amostras)", fim.saturating_duration_since(std::time::Instant::now()).as_secs_f32(), (sj / nj.max(1) as f64).sqrt(), nj);
                (janela, sj, nj) = (std::time::Instant::now(), 0.0, 0);
            }
        }
        stop.store(true, std::sync::atomic::Ordering::Relaxed);
        let _ = h.join();
        println!("amostras {n}, nível {:.4}", (soma / n.max(1) as f64).sqrt());
    }
    let _ = a;
    Ok(())
}
