# Praxis — QA Report (v0.1.0 → v0.2.0)

_Date: 2026-10-20 · Scope: full code audit, smoke/unit/GUI tests, cross-platform port,
transcription-quality and latency benchmarks on real human speech._

## Summary

| Area | v0.1.0 | v0.2.0 |
|---|---|---|
| Platforms | Linux only (PulseAudio/PipeWire) | Linux · macOS · Windows |
| Real-time continuous speech, all 16 languages (round 2) | not tested | GPU `large-v3-turbo`: 12% avg error, 0.8–2.3 s, keeps up 16/16 · CPU `small`: 24%, 1.8–3.0 s, 16/16 |
| GPU | NVIDIA CUDA only | NVIDIA CUDA · Apple Silicon (MLX) · AMD/Intel (whisper.cpp Vulkan, opt-in) · auto-detected |
| Automated tests | none | 115 fast tests (unit, smoke, GUI) + slow quality/latency gates |
| CI | none | GitHub Actions: Linux/macOS/Windows × Python 3.10/3.12 + benchmarks |
| Live transcription WER (pt, Whisper `small`, round 1) | **26.4%** | **16.7%** |
| Live transcription WER (en / es) | 8.7% / 13.8% | 5.3% / 6.9% |
| End-to-end latency (end of speech → first audio, p50, CPU) | — | **1.8–2.1 s** (Intel i9 CPU, `small`) |
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
| 3 | engine | Speech cut every 4 s mid-word, VAD state reset at each cut | Live WER pt 26.4% vs 15.5% for the same audio in one piece | Cut at the quietest point of the last 1.5 s without resetting VAD; limit raised to 6 s (measured below) |
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
| A — v0.1.0 segmentation (hard 4 s cut), ONNX VAD | 24.0% | 7.3% | 14.1% |
| B — + repetition guard | 24.0% | 7.3% | 14.1% |
| C — + 250 ms pre-roll | 19.4% | 7.8% | 11.6% |
| D — + smart cut, 4 s limit | 20.5% | 7.8% | 12.8% |
| **E — smart cut, 6 s limit (new default)** | **16.7%** | **5.3%** | **6.9%** |
| F — smart cut, 8 s limit | 14.3% | 5.3% | 6.6% |
| G — D without Whisper's internal VAD filter | 20.5% | 7.8% | 12.8% |

Whole-utterance WER (upper bound): pt 15.5% · en 3.9% · es 11.0%. Pre-roll recovers the first syllable (−4.6 pts pt). The smart cut only pays off with a longer limit: at 4 s it still splits most sentences; at 6 s live WER drops 30% (pt), 27% (en), 51% (es) vs v0.1.0. 8 s is ~2 pts better in pt but adds up to 2 s of waiting during uninterrupted speech, so 6 s is the default (`--max-segment` to change). The repetition guard changes nothing for `small` but removes the catastrophic `base` loops; disabling Whisper's internal VAD filter has no effect.

## Latency

_Machine: macOS-26.6.2-x86_64-i386-64bit · i386 · 16 cores · Python 3.12.15 · CUDA False_

Whisper model: `small` · backend: `cpu`

| Pair | N | VAD tail | ASR | MT | TTS 1st | **Total p50** | **Total p95** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 1666 | 56 | 110 | **2112 ms** | **2595 ms** |
| en->pt | 10 | 272 | 1392 | 48 | 92 | **1841 ms** | **1921 ms** |
| es->en | 10 | 256 | 1467 | 135 | 108 | **1962 ms** | **2182 ms** |

Stage values are p50 in ms. Total = end of speech → first translated audio sample ready (playback start).

End of speech → first translated audio, measured on the last live segment of 10 real utterances
per pair. ASR is ~80% of the total on this CPU; GPU backends (CUDA / MLX) are expected to cut that
stage several-fold but are not measured here. The VAD tail (256–288 ms) is the 200 ms silence the
VAD waits for plus 32 ms chunk granularity. Orchestration overhead (queues, threads, sentence split)
is asserted < 50 ms in `test_pipeline_overhead_latency`. All slow gates pass (`pytest -m slow`:
10 passed — live WER thresholds, no hallucination loops, translation sanity for 4 pairs, latency).

## Round 2 — real-time continuous speech, all 16 languages

_Machine: lab2 — Linux Mint 22.3, NVIDIA RTX 3050 6 GB, 16-thread CPU. Tool: `benchmarks/stream_test.py`._

**Method.** For every language Praxis understands (14 output languages + ja, ko as input only) a
~60–75 s recording of continuous real speech is fed to the real engine workers in real time,
32 ms at a time, exactly like a microphone. pt/es/fr/de/it/nl/pl use one audiobook reader with the
original pauses (Multilingual LibriSpeech), en a LibriSpeech chapter, and ru/zh/uk/tr/ar/hi/ja/ko
consecutive FLEURS sentences (speakers alternate). The test knows the script in advance and
monitors every segment: transcription errors (substituted / skipped / invented), how much the ASR
errors change the translation, the delay from the end of each speech segment to the first
translated audio, where that time goes (queue, transcription, translation, voice, waiting for the
previous speech), and whether the engine keeps up: typical delay ≤ 4 s, no growth between the
first and second half, ≤ 8 s of translation left when the speaker stops. Translated speech is
"played" for its real duration, so slow voices and long translations show up as lag.
Then `en →` each of the 13 other output languages tests translation + voice for every language.

| Hardware | Model | Avg error, 16 langs | pt | en | es | Typical delay | Keeps up |
|---|---|---:|---:|---:|---:|---:|---:|
| GPU (RTX 3050) | tiny | 48% | 29% | 6% | 19% | 0.4–1.6 s | 16/16 |
| GPU (RTX 3050) | base | 37% | 16% | 3% | 11% | 0.4–1.7 s | 15/16 |
| GPU (RTX 3050) | small | 24% | 8% | 2% | 3% | 0.5–2.0 s | 16/16 |
| GPU (RTX 3050) | medium | 17% | 5% | 4% | 5% | 0.8–2.3 s | 16/16 |
| GPU (RTX 3050) | large-v3 | 12% | 6% | 3% | 3% | 1.1–2.7 s | 16/16 |
| GPU (RTX 3050) | **large-v3-turbo** | 12% | 5% | 1% | 3% | 0.8–2.3 s | 16/16 |
| CPU (lab2) | tiny | 53% | 32% | 7% | 18% | 0.6–1.6 s | 16/16 |
| CPU (lab2) | base | 39% | 14% | 6% | 12% | 0.8–2.2 s | 15/16 |
| CPU (lab2) | **small** | 24% | 8% | 3% | 3% | 1.8–3.0 s | 16/16 |
| CPU (lab2) | medium | 16% | 5% | 5% | 5% | 4.2–16.0 s | 0/16 |
| CPU (lab2) | large-v3-turbo | 12% | 5% | 2% | 3% | 6.8–25.7 s | 0/16 |

Error = share of words transcribed wrong, skipped or invented (characters for zh/ja), averaged over 16 languages.
**Bold** = what `--model auto` now picks: `large-v3-turbo` with a GPU, `small` on CPU.

### Problems the test exposed — and what was done

| # | Problem (how it showed up) | Fix | Before → after |
|---|---|---|---|
| 1 | The engine waited for each translation to finish **playing** before transcribing the next segment (CPU `small`: 4–6 s delay, growing +38…+94 ms per second) | Ordered player thread: transcription of the next segment overlaps playback | delay 5.1 → 2.0 s (pt), keeps up 0/3 → 16/16 |
| 2 | Long unpunctuated passages broke **translation** into a loop ("I have not been able to do so…") | Sentences > 30 words (60 chars zh/ja) split at commas, then by length | it→en fidelity 8.5 → 54.9 |
| 3 | A filter dropped **real speech** whenever Whisper's no-speech score was ≥ 0.5 (0.53–0.59 on real phrases) | Whisper's own rule: drop only if not-speech **and** low confidence | lost phrases restored (pt, it, uk) |
| 4 | 0.1–0.8 s leftovers after a cut came back **empty**, losing syllables ("Professor" → "ofessor") | Leftovers glued to the next segment (or sent after 1 s of silence) | empty segments 10 → 3 |
| 5 | **German** translation spoken at 146% of the original length → 38 s backlog | Default German voice "MLS" (10.8 letters/s) → "Thorsten" (19.9); slow voices auto-calibrated to ≥ 15 letters/s | 146% → 82%, keeps up |
| 6 | **Arabic / Hindi / Dutch** translations longer than the speech, falling behind | Adaptive speaking rate: the voice speeds up (×1.15 → ×1.4) as playback piles up | en→ar 121% → 102%, en→nl 111% → 92%, all 13 keep up |
| 7 | Broken characters "�" from Whisper reached translation and speech (Hindi) | Stripped before translation | — |
| 8 | Our own metric split Hindi/Arabic words at vowel marks (hid real errors) | Normalisation keeps combining marks; results re-scored | hi 46% → 70% (true value) |
| 9 | `medium` skipped whole phrases in Spanish | Resolved by #3/#4 | 0 skipped phrases in any language |

### Still limited (model quality, not engine bugs)

- On a CPU the most accurate real-time model is `small`: fine for pt/en/es (3–8% errors) but
  16–37% in fr, de, it, zh, nl, tr, ar, ja, ko and ~70% in Hindi. The app now warns about this and
  points to the GPU numbers (e.g. fr 25% on CPU vs 8% with a GPU).
- Even `large-v3-turbo` on a GPU errs 27% in Korean and 34% in Hindi (`large-v3`: 24% / 26%).
- A single segment can still spike to 4–7 s when a long sentence is followed by more speech.
- Corpus: ~1 min per language, read speech. Spontaneous, noisy call audio will score worse.

## GPU support

`praxis_accel.py` picks the backend per machine (override: `--device` / `PRAXIS_DEVICE`):
CUDA → faster-whisper/CTranslate2; Apple Silicon → mlx-whisper; AMD/Intel GPU → whisper.cpp
built with Vulkan (opt-in build); otherwise CPU. Piper uses CUDA / DirectML / CoreML providers when
available; OmniVoice uses CUDA or MPS.

Measured on this machine (Intel i9 + AMD Radeon Pro 5500M): whisper.cpp **Metal** returned `","`
for a 4 s Portuguese sentence and took 2.85 s vs 2.10 s on CPU — so Intel Macs are pinned to CPU.
CI has no GPUs: selection logic is tested for every hardware family with mocks
(`tests/test_accel.py`). **CUDA was verified on real hardware** (lab2, RTX 3050) — which exposed that the
pip-installed cuBLAS/cuDNN were not found without `LD_LIBRARY_PATH` (Whisper silently fell back to CPU;
fixed by `ensure_cuda_libs()`). MLX and Vulkan remain unverified on real hardware.

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
