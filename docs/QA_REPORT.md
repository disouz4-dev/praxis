# Praxis — QA Report (v0.1.0 → v0.2.0)

_Date: 2026-10-20 · Scope: full code audit, smoke/unit/GUI tests, cross-platform port,
transcription-quality and latency benchmarks on real human speech._

## Summary

| Area | v0.1.0 | v0.2.0 |
|---|---|---|
| Platforms | Linux only (PulseAudio/PipeWire) | Linux · macOS · Windows |
| GPU | NVIDIA CUDA only | NVIDIA CUDA · Apple Silicon (MLX) · AMD/Intel (whisper.cpp Vulkan, opt-in) · auto-detected |
| Automated tests | none | 86 fast tests (unit, smoke, GUI) + slow quality/latency gates |
| CI | none | GitHub Actions: Linux/macOS/Windows × Python 3.10/3.12 + benchmarks |
| Live transcription WER (pt, Whisper `small`) | **26.4%** | **19.4%** |
| Live transcription WER (en / es) | 8.7% / 13.8% | 7.8% / 11.6% |
| End-to-end latency (end of speech → first audio, p50, CPU) | — | pending (benchmark not run yet — see Latency) |
| PyTorch required | yes (~550 MB) | no (only for optional voice cloning) |

## How it was tested

* **Static audit** of all 5.8k lines (engine, UI, installer) — every finding below has a file/line,
  a failure scenario, and (where possible) a regression test.
* **Smoke**: `praxis.py --check` / `--list-devices` on every OS in CI; the real UI is built,
  tab-switched in several UI languages, theme-toggled, saved and closed (`tests/test_gui_smoke.py`).
* **Unit**: parsers (pactl, xrandr), resampler, loopback-driver detection, VAD segmentation,
  sentence split, translation pivot, config persistence, atomic downloads, full pipeline with fakes.
* **Real speech**: 34 clips from 34 different volunteer speakers in pt / en / es
  (Multilingual LibriSpeech + LibriSpeech, CC BY 4.0) with human reference transcripts.
  Quality is measured as WER/CER in two modes: the whole utterance (upper bound) and **live** —
  streamed chunk-by-chunk through the engine's real `vad_worker`, exactly as during a call.
* **Latency**: per stage (VAD tail, ASR, MT, TTS first sentence) on the same real speech.

## Critical bugs found and fixed

| # | Where | Bug | Impact | Fix |
|---|---|---|---|---|
| 1 | engine | PyTorch (Silero VAD, Argos→stanza) and CTranslate2 (Whisper) load **two OpenMP runtimes** | **Segfault on the first transcription on macOS** | Engine is now torch-free: Silero VAD on ONNX Runtime, Argos models run directly on CTranslate2 |
| 2 | engine | Argos/CTranslate2 `compute_type="auto"` picks int8 on many CPUs | **es→en (and every es→X pivot) outputs garbage** ("mainstremainstre…") — also affects v0.1.0 | `compute_type="default"`; translation sanity gate in CI |
| 3 | engine | Speech cut every 4 s mid-word, VAD state reset at each cut | Live WER pt 26.4% vs 15.5% for the same audio in one piece | Cut at the quietest point of the last 1.5 s without resetting VAD; limit tuned with data (below) |
| 4 | engine | No pre-roll: buffer starts *after* the VAD triggers | First syllable of every phrase lost ("a soberba" → "sobre a") | 250 ms pre-roll |
| 5 | engine | Whisper hallucination loops on short cut segments | Up to 991% WER on a single clip ("o que é o que é …" ×100), translated and spoken aloud | Repetition guard on every transcript |
| 6 | UI | `pw-metadata` called unguarded at startup and close | **App can't start** without PipeWire (any macOS/Windows, PulseAudio-only Linux); can't close if it hangs | Platform layer, no-op elsewhere |
| 7 | UI | Pillow imported unguarded in the splash, but not in the installer's deps | **App can't start** on a clean install (reproduced on macOS) | Optional Pillow, Tk-native PNG; Pillow added to requirements |
| 8 | UI | Clone-tab audio callback calls Tk ~350×/s from the PortAudio thread | Hang on close / "main thread is not in main loop" (reproduced) | Main-thread poll at 30 Hz |
| 9 | engine | Virtual devices only removed on clean exit | Every failed start leaks PulseAudio modules (duplicate "Praxis_Microfone" devices) | `try/finally` teardown |
| 10 | engine | One exception in ASR/MT kills the direction's worker thread | Translation silently stops for the rest of the call | Per-segment error handling + `error` event |

## Other bugs fixed

**Engine (`praxis.py`)**
- `tempfile.mktemp` WAV written per segment and never deleted (disk leak, insecure); OmniVoice
  reference shared by both directions through globals (race) → per-voice, per-direction file.
- Bilateral + PTT: the peer's audio was gated by *your* PTT key, and releasing it paused both
  directions → peer always uses VAD; pause/resume affects both.
- `reload_voice` with a missing path was silently ignored (UI stuck on "Aplicando…") → error event.
- `--voice-out` validation, `--gate-threshold` range check, `--check` and `--list-devices` commands.

**UI (`praxis_config.py`)**
- Tab switch used `"Config" in label` → the Config tab never came back in de/ru/zh/pl/uk/tr/ar/hi.
- UI language never persisted; `_save()` didn't update the in-memory config, so toggling the theme
  later overwrote the saved settings with the startup ones.
- Voice "Tugão (PT)" could never be downloaded (non-ASCII URL). Interrupted downloads left a
  partial `.onnx` that showed as installed → atomic `.part` + rename, URL quoting.
- `_toggle_monitor` defined twice: the Clone-tab monitor switch toggled the *engine* monitor and
  mic monitoring never worked.
- Clone test status messages were all dropped (`after(0, configure, kw)` passed a dict positionally).
- Trimming wrote every reference to the same `/tmp/ov_ref_trim.wav` → importing a long WAV and
  generating saved a 5 s clone. All `/tmp/...` fixed paths → private per-user temp dir.
- ffmpeg missing / timeout / invalid WAV crashed the import flow; recording save errors left
  "Salvando…" forever.
- Engine relaunch: old reader thread posted stale events into the new session; `terminate()` without
  `wait()` left zombies; log file handles leaked; a crashed engine left the UI stuck on "Rodando…"
  with no message → graceful stop (`stop` command → SIGTERM → SIGKILL), crash dialog with log tail.
- Bilateral transcripts from the other person were shown as yours (`dir` ignored) → marked "←".
- `pactl set-default-source/sink` permanently changed the system defaults → restored on close
  (Linux), explicit device indices elsewhere.
- Corrupt/hand-edited config crashed startup (`None`/string where a number was expected);
  non-atomic save → type coercion + atomic write.
- Window taller than 768 px screens; splash progress thread touched Tk off the main thread;
  mono output stream rejected by CoreAudio (`AUHAL -50`); dead `MonitorWindow` class removed.
- App icon: the Dock/taskbar showed Python's rocket → Praxis icon (PNG/ICO/ICNS), process name on
  macOS, `Praxis.app` bundle, Linux `.desktop`, Windows shortcuts.

**Installer**
- Only `apt-get`; didn't copy `assets/` (no logo/icon after install); missing deps (`soundfile`,
  `pynput`, `pillow`, `requests`); unconditional PyTorch install → `install.sh` for
  apt/dnf/pacman/zypper/Homebrew, `install.ps1` for Windows, self-check at the end.

## Transcription quality (real speech, Whisper `small`, CPU)

| Model | Lang | Clips | WER full utterance | WER live (v0.1.0 engine) | RTF |
|---|---|---:|---:|---:|---:|
| base | pt | 10 | 28.7% | 120.9% | 0.06 |
| base | en | 12 | 5.8% | 10.7% | 0.08 |
| base | es | 12 | 11.0% | 93.4% | 0.06 |
| small | pt | 10 | 15.5% | 26.4% | 0.18 |
| small | en | 12 | 3.9% | 8.7% | 0.23 |
| small | es | 12 | 11.0% | 13.8% | 0.18 |

_Machine: Intel Core i9-9980HK (MacBook Pro 2019), CPU int8, Python 3.12. RTF = ASR time ÷ audio time._ The `base` model's live WER above 100% comes from hallucination loops on 4 s cuts (one clip: 991%).

### What each change bought (live WER)

| Variant | pt | en | es |
|---|---:|---:|---:|
| A — ONNX VAD, hard 4 s cut (v0.1.0 segmentation) | 24.0% | 7.3% | 14.1% |
| B — + repetition guard | 24.0% | 7.3% | 14.1% |
| C — + 250 ms pre-roll | 19.4% | 7.8% | 11.6% |
| D–G — smart cut at 4/6/8 s, Whisper internal VAD off | _running — results will be added to this report_ | | |

Whole-utterance WER (upper bound): pt 15.5% · en 3.9% · es 11.0%. The guard changes nothing for `small` (no loops) but removes the catastrophic `base` loops. The pre-roll alone recovers 4.6 WER points in Portuguese.

## Latency

The latency benchmark (`python benchmarks/run_benchmarks.py latency`) and the slow CI gates (`pytest -m slow`) are in place but have **not been run yet** in this round; results will be added here. Unit-level: orchestration overhead (queues, threads, sentence split) between a segment and its first audio is asserted < 50 ms in `test_pipeline_overhead_latency`.

## GPU support

`praxis_accel.py` picks the backend per machine (override: `--device` / `PRAXIS_DEVICE`):
CUDA → faster-whisper/CTranslate2; Apple Silicon → mlx-whisper; AMD/Intel GPU → whisper.cpp
built with Vulkan (opt-in build); otherwise CPU. Piper uses CUDA / DirectML / CoreML providers when
available; OmniVoice uses CUDA or MPS.

Measured on this machine (Intel i9 + AMD Radeon Pro 5500M): whisper.cpp **Metal** returned `","`
for a 4 s Portuguese sentence and took 2.85 s vs 2.10 s on CPU — so Intel Macs are pinned to CPU.
CI has no GPUs: selection logic is tested for every hardware family with mocks
(`tests/test_accel.py`); CUDA, MLX and Vulkan execution are **not yet verified on real hardware**.

## Known issues (not fixed in this round)

- Some UI strings are still hard-coded in Portuguese (download dialog, monitor panel, splash).
- `ja`/`ko` have no localized names in the language menus.
- Recording restarted within 1 s runs two timer chains (auto-stop at ~7 s).
- Capturing a *letter* key as PTT fails (pynput `KeyCode` has no `.name`); pynput global hooks
  don't work on Wayland.
- OmniVoice: parallel "Gerar"/"Testar" can load the model twice (GPU OOM); the Clone tab reloads a
  Whisper model for every transcription; deleting a clone has no confirmation.
- OmniVoice (optional) still needs PyTorch, so on macOS it can hit the OpenMP conflict (#1) when
  used together with Whisper in one process.
- Argos `en→pt` produces European Portuguese ("estás", "a testar").
