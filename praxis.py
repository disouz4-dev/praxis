#!/usr/bin/env python3
"""Praxis — tradutor de voz em tempo real com microfone virtual (bilateral).
Real-time voice translator with virtual microphone (bilateral mode).
"""

import argparse
import json
import os
import queue
import re
import signal
import sys
import threading
import time
from collections import deque
from pathlib import Path

import numpy as np
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

import praxis_platform as plat

# ── Constantes de áudio e PulseAudio / Audio and PulseAudio constants ─────────
SR         = 16000          # taxa de amostragem Whisper / Whisper sample rate
VAD_CHUNK  = 512            # ~32 ms @ 16 kHz — janela do VAD / VAD window size
SILENCE_MS = 200            # silêncio para cortar segmento / silence to cut segment
MAX_SEG_S  = 6.0            # corte em falas longas sem pausa / max segment length
                            # (benchmarked: 4 s → pt 20.5% WER, 6 s → 16.7%, 8 s → 14.3%)
PREROLL_S  = 0.25           # áudio antes do "start" do VAD / audio kept before VAD start (onset)
MIN_SEG_S  = 0.8            # pedaços menores entram no próximo trecho / shorter pieces join the next one
CARRY_MAX_WAIT_S = 1.0      # …mas saem sozinhos após 1 s de silêncio ("Sim." não fica preso)
SMART_CUT_WINDOW_S = 1.5    # corte longo no ponto mais silencioso / long-segment cut searches this tail
SINK_OUT   = plat.SINK_OUT  # null sink → microfone virtual de saída / outbound virtual mic
SRC_MIC    = plat.SRC_MIC   # nome da fonte de áudio virtual / virtual audio source name
SRC_DESC   = plat.SRC_DESC  # descrição legível no pavucontrol / human-readable description
SINK_IN    = plat.SINK_IN   # null sink → captura áudio do interlocutor / inbound capture sink

# ── Estado global compartilhado entre threads / Global state shared between threads ──
_active = threading.Event()     # sinaliza se tradução está ativa / signals if translation is active
_peer_active = threading.Event()  # peer direction: follows pause/resume but never PTT
_stop   = threading.Event()     # sinaliza encerramento do programa / signals program shutdown
_active.set()
_peer_active.set()

# Audio backend + virtual devices (set in main) / platform audio backend
_backend: "plat.AudioBackend | None" = None
_vmic: "plat.VirtualMic" = plat.VirtualMic(target=SINK_OUT, mic_label=SRC_DESC)

# Filas de áudio bruto (chunks VAD) / Raw audio queues (VAD chunks)
_out_audio_q: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=200)  # microfone do usuário / user mic
_in_audio_q:  "queue.Queue[np.ndarray]" = queue.Queue(maxsize=200)  # áudio do interlocutor / peer audio

# Filas de segmentos de fala detectados / Detected speech segment queues
_out_seg_q:   "queue.Queue[np.ndarray]" = queue.Queue()
_in_seg_q:    "queue.Queue[np.ndarray]" = queue.Queue()

# PTT (Push-to-Talk): sinaliza VAD para enviar buffer ao soltar o botão
# PTT: signals VAD to flush buffer when button is released
_ptt_flush    = threading.Event()

# Histórico de transcrições para a TUI / Transcript history for TUI
_transcripts: deque = deque(maxlen=8)
_tr_lock = threading.Lock()
_ui_state: dict = {"status": "INICIANDO", "src": "pt", "tgt": "en", "bilateral": False}
_json_out: bool = False  # modo JSON para integração com a UI Electron / JSON mode for Electron UI

# Referência mutável para hot-swap de voz sem reiniciar Whisper
# Mutable reference for voice hot-swap without restarting Whisper
_piper_out_ref: list = [None]   # [PiperVoice | OmniVoiceEngine]
_piper_lock = threading.Lock()

console = Console()


def _emit(data: dict) -> None:
    """Emite evento JSON para o processo pai (UI Electron) quando em modo --json-out.
    Emits JSON event to parent process (Electron UI) when in --json-out mode."""
    if _json_out:
        print(json.dumps(data, ensure_ascii=False), flush=True)


# ── Audio (delegated to praxis_platform) ─────────────────────────────────────

def _get_backend() -> "plat.AudioBackend":
    global _backend
    if _backend is None:
        _backend = plat.get_backend()
    return _backend


def setup_virtual_devices(bilateral: bool) -> "plat.VirtualMic":
    """Creates (Linux) or locates (macOS/Windows) the virtual microphone."""
    global _vmic
    _vmic = _get_backend().setup_virtual_mic(bilateral)
    return _vmic


def teardown_virtual_devices() -> None:
    """Removes virtual devices created by Praxis (no-op where nothing was created)."""
    if _backend is not None:
        _backend.teardown()


def resolve_mic(mic_arg: str | None) -> str | None:
    """Linux: 'dev:left/right' → mono remap source. Elsewhere the channel is
    selected at capture time, so the id is returned unchanged."""
    return _get_backend().resolve_mic(mic_arg)


def play_pcm(pcm: bytes, rate: int, *devices: str | None) -> None:
    """Plays s16le mono PCM on one or more devices simultaneously."""
    _get_backend().play_pcm_multi(pcm, rate, devices)


# ── TUI ───────────────────────────────────────────────────────────────────────

def build_panel() -> Panel:
    src    = _ui_state["src"].upper()
    tgt    = _ui_state["tgt"].upper()
    status = _ui_state["status"]
    bilat  = _ui_state["bilateral"]

    status_color = {"TRADUZINDO": "green", "PAUSADO": "yellow"}.get(status, "dim")

    table = Table(box=None, show_header=False, expand=True, padding=(0, 1))
    table.add_column("c", ratio=1)

    direction_line = f"{src} → {tgt}"
    if bilat:
        direction_line += f"  [dim]│[/dim]  {tgt} → {src}"
    table.add_row(f"[{status_color}]● {status}[/{status_color}]   [dim]{direction_line}[/dim]")
    table.add_row("")

    with _tr_lock:
        recent = list(_transcripts)

    if not recent:
        table.add_row("[dim]Aguardando fala...[/dim]")
    else:
        for direction, original, translated in recent[-4:]:
            arrow  = "→" if direction == "out" else "←"
            color  = "cyan" if direction == "out" else "magenta"
            table.add_row(
                f"[{color}]{arrow}[/{color}] [dim]{original[:90]}[/dim]"
            )
            table.add_row(f"   [bold]{translated[:90]}[/bold]")

    table.add_row("")
    table.add_row("[dim]ENTER: pausar/retomar   │   Ctrl+C: sair[/dim]")

    hints = [f"Mic virtual: [bold]{_vmic.mic_label}[/bold]"]
    if bilat:
        hints.append(f"Bilateral: redirecione saída deles para [bold]{_vmic.peer_label}[/bold]")
        hints.append("[dim]Use fone de ouvido para evitar feedback[/dim]")

    return Panel(
        table,
        title="[bold cyan]✦  Praxis[/bold cyan]",
        subtitle=f"[dim]{' │ '.join(hints)}[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
    )


# ── Workers ───────────────────────────────────────────────────────────────────

def capture_worker(device: str | None,
                   audio_q: "queue.Queue[np.ndarray]",
                   active: threading.Event,
                   delay: float = 0.0) -> None:
    """Captures mono 16 kHz audio from `device` → audio_q (VAD_CHUNK samples).

    Sempre drena a captura mesmo quando inativo — evita acúmulo de áudio antigo
    no buffer do SO que seria liberado na próxima ativação (bug PTT/gate).
    Always drains capture while inactive so stale audio is never replayed.
    """
    if delay:
        time.sleep(delay)
    try:
        cap = _get_backend().open_capture(device, SR, VAD_CHUNK)
    except Exception as e:
        _emit({"e": "error", "msg": f"audio capture failed ({device or 'default'}): {e}"})
        console.print(f"[red]Captura de áudio falhou:[/red] {e}")
        return
    try:
        while not _stop.is_set():
            data = cap.read()
            if not data:
                break
            if not active.is_set():
                continue  # descarta: drena mas não enfileira / drain, don't enqueue
            arr = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            if len(arr) == VAD_CHUNK:
                try:
                    audio_q.put_nowait(arr.copy())
                except queue.Full:
                    pass
    finally:
        cap.close()


def mic_worker(mic_device: str | None) -> None:
    """User microphone → _out_audio_q."""
    capture_worker(mic_device, _out_audio_q, _active)


def monitor_worker() -> None:
    """Peer audio (bilateral) → _in_audio_q."""
    capture_worker(_vmic.peer_capture, _in_audio_q, _peer_active, delay=1.0)


class OnnxSileroVAD:
    """Streaming Silero VAD on onnxruntime — same API as silero's VADIterator.

    Uses the Silero v6 ONNX model bundled with faster-whisper, so the engine
    needs no PyTorch. (PyTorch + CTranslate2 in one process load two OpenMP
    runtimes and crash Whisper on macOS.)"""

    CONTEXT = 64

    def __init__(self, threshold: float = 0.5, sampling_rate: int = 16000,
                 min_silence_duration_ms: int = 100, speech_pad_ms: int = 30) -> None:
        import onnxruntime
        from faster_whisper.utils import get_assets_path
        opts = onnxruntime.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        opts.log_severity_level = 4
        self.session = onnxruntime.InferenceSession(
            str(Path(get_assets_path()) / "silero_vad_v6.onnx"),
            providers=["CPUExecutionProvider"], sess_options=opts)
        self.threshold = threshold
        self.sr = sampling_rate
        self.min_silence = sampling_rate * min_silence_duration_ms / 1000
        self.pad = sampling_rate * speech_pad_ms / 1000
        self.reset_states()

    def reset_states(self) -> None:
        self._h = np.zeros((1, 1, 128), np.float32)
        self._c = np.zeros((1, 1, 128), np.float32)
        self._ctx = np.zeros((1, self.CONTEXT), np.float32)
        self.triggered = False
        self.temp_end = 0
        self.current_sample = 0

    def prob(self, chunk: np.ndarray) -> float:
        x = np.asarray(chunk, np.float32).reshape(1, -1)
        inp = np.concatenate([self._ctx, x], axis=1)
        out, self._h, self._c = self.session.run(None, {"input": inp, "h": self._h, "c": self._c})
        self._ctx = x[:, -self.CONTEXT:]
        return float(np.asarray(out).reshape(-1)[0])

    def __call__(self, chunk, return_seconds: bool = False):
        if hasattr(chunk, "numpy"):
            chunk = chunk.numpy()
        n = len(chunk)
        self.current_sample += n
        p = self.prob(chunk)
        if p >= self.threshold and self.temp_end:
            self.temp_end = 0
        if p >= self.threshold and not self.triggered:
            self.triggered = True
            start = max(0, self.current_sample - self.pad - n)
            return {"start": start / self.sr if return_seconds else int(start)}
        if p < self.threshold - 0.15 and self.triggered:
            if not self.temp_end:
                self.temp_end = self.current_sample
            if self.current_sample - self.temp_end < self.min_silence:
                return None
            end = self.temp_end + self.pad - n
            self.temp_end = 0
            self.triggered = False
            return {"end": end / self.sr if return_seconds else int(end)}
        return None


def load_silero_vad():
    """→ (model, VADIterator-compatible factory). ONNX (no torch) when possible."""
    try:
        import onnxruntime  # noqa: F401
        from faster_whisper.utils import get_assets_path
        if (Path(get_assets_path()) / "silero_vad_v6.onnx").exists():
            return None, lambda _model, **kw: OnnxSileroVAD(**kw)
    except Exception:
        pass
    import torch
    _local = Path.home() / ".cache/torch/hub/snakers4_silero-vad_master"
    if _local.exists():
        model, utils = torch.hub.load(str(_local), "silero_vad", source="local",
                                      force_reload=False, onnx=False)
    else:
        model, utils = torch.hub.load("snakers4/silero-vad", "silero_vad",
                                      force_reload=False, onnx=False, trust_repo=True)
    return model, utils[3]


def vad_worker(audio_q:       "queue.Queue[np.ndarray]",
               seg_q:         "queue.Queue[np.ndarray]",
               mode:          str   = "vad",
               gate_threshold: float = 0.10,
               active:        "threading.Event | None" = None,
               ptt_flush:     "threading.Event | None" = None,
               vad_factory=None,
               max_seg_s:     "float | None" = None,
               smart_cut:     bool = True,
               preroll_s:     "float | None" = None) -> None:
    """Detecta segmentos de fala usando Silero VAD e enfileira em seg_q.
    Detects speech segments using Silero VAD and enqueues them in seg_q.

    Modos / modes:
      vad  — detecção automática por probabilidade de fala / automatic speech probability detection
      gate — threshold RMS simples / simple RMS threshold
      ptt  — push-to-talk via _ptt_flush / push-to-talk via _ptt_flush event

    Segment quality (measured with benchmarks/run_benchmarks.py asr):
      * pre-roll — the VAD fires a chunk or two *after* speech begins; the
        last PREROLL_S of audio is prepended so the first syllable survives.
      * smart cut — long speech is split at the quietest chunk of the last
        SMART_CUT_WINDOW_S instead of mid-word, without resetting the VAD.
    """
    max_seg_s = MAX_SEG_S if max_seg_s is None else max_seg_s
    preroll_s = PREROLL_S if preroll_s is None else preroll_s
    active    = active if active is not None else _active
    ptt_flush = ptt_flush if ptt_flush is not None else _ptt_flush
    if vad_factory is None:
        model, VADIterator = load_silero_vad()
        vad = VADIterator(model, sampling_rate=SR, threshold=0.5,
                          min_silence_duration_ms=SILENCE_MS)
    else:
        vad = vad_factory()

    buf: list[np.ndarray] = []
    speaking = False
    buf_dur  = 0.0
    ptt_mode = (mode == "ptt")
    chunk_s  = VAD_CHUNK / SR
    preroll: deque = deque(maxlen=max(0, int(round(preroll_s / chunk_s))) or None)
    if preroll_s <= 0:
        preroll = deque(maxlen=0)

    def _cut_long() -> None:
        """Emits a long segment but keeps listening (speech continues)."""
        nonlocal buf, buf_dur
        k = min(len(buf) - 1, int(SMART_CUT_WINDOW_S / chunk_s))
        if smart_cut and k > 0:
            tail = buf[-k:]
            energy = [float(np.mean(c.astype(np.float32) ** 2)) for c in tail]
            j = len(buf) - k + int(np.argmin(energy))
            seg, rest = buf[:j + 1], buf[j + 1:]
        else:
            seg, rest = buf, []
        _emit_seg(seg)
        buf, buf_dur = rest, len(rest) * chunk_s

    carry: list[np.ndarray] = []       # tiny leftover after a cut, glued to the next segment
    carry_age = 0                      # silent chunks since the leftover was kept

    def _emit_seg(chunks: list[np.ndarray], force: bool = False) -> None:
        nonlocal carry, carry_age
        chunks = carry + chunks
        carry, carry_age = [], 0
        if not chunks:
            return
        if not force and len(chunks) * chunk_s < MIN_SEG_S:
            # Too short for Whisper on its own (it returns nothing and the
            # syllable is lost) — keep it for the next segment instead.
            carry = chunks
            return
        seg_q.put(np.concatenate(chunks))

    def _flush_buf(force: bool = False) -> None:
        nonlocal buf, buf_dur, speaking
        if buf or (force and carry):
            _emit_seg(buf, force=force)
        buf, buf_dur, speaking = [], 0.0, False
        vad.reset_states()

    while not _stop.is_set():
        # PTT flush: botão solto → envia buffer atual e desativa
        if ptt_mode and ptt_flush.is_set():
            ptt_flush.clear()
            _flush_buf(force=True)             # button released: send everything now
            active.clear()

        if not active.is_set():
            # Drena fila e DESCARTA buffer interno — áudio antes do botão/gate não deve
            # ser enviado ao pipeline quando o modo voltar a estar ativo.
            while not audio_q.empty():
                try:
                    audio_q.get_nowait()
                except queue.Empty:
                    break
            if speaking:
                buf, buf_dur, speaking = [], 0.0, False
                vad.reset_states()
            preroll.clear()
            time.sleep(0.05)
            continue

        try:
            chunk = audio_q.get(timeout=0.2)
        except queue.Empty:
            continue

        # Gate mode: ignora chunks abaixo do threshold de RMS
        if mode == "gate":
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            if rms < gate_threshold:
                if speaking:
                    _flush_buf()   # envia fala já capturada acima do gate
                else:
                    vad.reset_states()  # sem fala: limpa estado VAD para não vazar
                continue

        i16 = (chunk * 32767).clip(-32768, 32767).astype(np.int16)
        ev = vad(chunk, return_seconds=False)
        if ev and "start" in ev and not speaking:
            speaking = True
            buf = list(preroll)                 # onset that preceded the trigger
            buf_dur = len(buf) * chunk_s
            preroll.clear()

        if speaking:
            buf.append(i16)
            buf_dur += chunk_s
        else:
            preroll.append(i16)
            if carry:
                carry_age += 1
                if carry_age * chunk_s >= CARRY_MAX_WAIT_S:
                    _emit_seg([], force=True)   # short utterance followed by silence

        if ev and "end" in ev and speaking:
            _flush_buf()
        elif speaking and buf_dur >= max_seg_s:
            _cut_long()


_SENT_SPLIT = re.compile(r'(?<=[.!?…])\s+')

# Parâmetros do Whisper usados em produção / Whisper decoding options used live
WHISPER_OPTS: dict = dict(
    beam_size=1,
    condition_on_previous_text=False, without_timestamps=True,
    temperature=0,
    no_speech_threshold=0.5,
    log_prob_threshold=-1.0,
    compression_ratio_threshold=2.4,
    vad_filter=True,
    vad_parameters={"min_silence_duration_ms": 300},
)
_NOISE_ONLY = {"", ".", ",", "...", "!", "?", "…"}
NO_SPEECH_DROP = 0.6       # Whisper's default no_speech_threshold
LOGPROB_DROP = -1.0        # … combined with low confidence in the decoded text


def collapse_repetitions(text: str, max_repeats: int = 2) -> str:
    """Removes Whisper hallucination loops ("o que é o que é o que é …").

    Any 1–8-word phrase repeated back-to-back more than `max_repeats` times
    is kept only `max_repeats` times."""
    words = text.split()
    if len(words) < 4:
        return text
    changed = True
    while changed:
        changed = False
        for n in range(1, 9):
            i = 0
            out: list[str] = []
            while i < len(words):
                gram = [w.lower().strip(".,!?¿¡;:…") for w in words[i:i + n]]
                reps = 1
                while words[i + reps * n:i + (reps + 1) * n] and \
                        [w.lower().strip(".,!?¿¡;:…") for w in
                         words[i + reps * n:i + (reps + 1) * n]] == gram:
                    reps += 1
                if reps > max_repeats and len(gram) == n:
                    out.extend(words[i:i + n * max_repeats])
                    i += reps * n
                    changed = True
                else:
                    out.append(words[i])
                    i += 1
            words = out
    return " ".join(words)


def transcribe_segment(whisper, audio_f32: np.ndarray, lang: str) -> str:
    """ASR of one speech segment (float32, 16 kHz) → text ('' = no speech).

    Shared by the live pipeline and the benchmarks so both measure the same code."""
    segs, _info = whisper.transcribe(audio_f32, language=lang, **WHISPER_OPTS)
    # Drop a segment only when Whisper both thinks it is not speech AND is unsure
    # of the text (Whisper's own rule). Filtering on no_speech_prob alone threw
    # away correctly transcribed speech (measured: 0.53–0.59 on real phrases).
    text = " ".join(s.text for s in segs
                    if not (s.no_speech_prob > NO_SPEECH_DROP
                            and getattr(s, "avg_logprob", 0.0) < LOGPROB_DROP)).strip()
    # Whisper can split a multi-byte character between tokens (seen in Hindi):
    # never pass the resulting "�" on to translation and speech.
    text = re.sub(r"\s{2,}", " ", text.replace("\ufffd", "")).strip()
    text = collapse_repetitions(text)
    return "" if text in _NOISE_ONLY else text


def _split_sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]
    return parts or [text]


# Adaptive speaking rate: when translated speech piles up (languages whose
# translation is longer than the original — e.g. en→ar measured at 121%), the
# voice speaks faster to catch up instead of drifting further behind.
RATE_STEPS = ((1.5, 1.0), (4.0, 0.87), (8.0, 0.77), (float("inf"), 0.7))   # (backlog ≤ s, length_scale)


def speech_length_scale(backlog_s: float) -> float:
    """Piper length_scale for the current playback backlog (1.0 = normal speed)."""
    for limit, scale in RATE_STEPS:
        if backlog_s <= limit:
            return scale
    return RATE_STEPS[-1][1]


def _synthesize(voice, text: str, length_scale: float):
    """Voice synthesis at a given speed; voices without speed control
    (OmniVoice, test doubles) fall back to their normal speed. The voice's own
    calibration (praxis_rate_scale, for slow voices) is applied on top."""
    length_scale *= getattr(voice, "praxis_rate_scale", 1.0)
    if length_scale != 1.0:
        try:
            from piper.config import SynthesisConfig
            base = getattr(getattr(voice, "config", None), "length_scale", None) or 1.0
            return voice.synthesize(text, syn_config=SynthesisConfig(length_scale=base * length_scale))
        except (ImportError, TypeError):
            pass
    return voice.synthesize(text)


def pipeline_worker(
    seg_q: "queue.Queue[np.ndarray]",
    whisper,
    piper,
    src: str,
    tgt: str,
    direction: str,              # "out" (usuário) | "in" (interlocutor) / "out" (user) | "in" (peer)
    monitor: bool = False,
    monitor_output: str | None = None,
) -> None:
    """Pipeline completo: ASR (Whisper) → tradução (Argos) → TTS streaming por frase → play.
    Full pipeline: ASR (Whisper) → translation (Argos) → per-sentence streaming TTS → play.

    O áudio traduzido toca numa thread própria (em ordem, sem sobreposição):
    enquanto uma frase é falada, o Whisper já transcreve o próximo trecho.
    Translated audio plays on its own thread (in order, never overlapping), so
    Whisper transcribes the next segment while the previous one is spoken.
    Measured with benchmarks/stream_test.py: in the old serial design (ASR →
    MT → TTS → wait for playback → next) a CPU running `small` fell further
    and further behind continuous speech (lag +38…+94 ms per second).
    """
    if direction == "out":
        targets = (_vmic.target, monitor_output) if monitor else (_vmic.target,)
    else:
        targets = (monitor_output,)
    out_q: "queue.Queue[tuple[bytes, int] | None]" = queue.Queue()
    backlog = {"s": 0.0}                      # seconds of translated speech not yet played
    backlog_lock = threading.Lock()

    def _player() -> None:
        while True:
            try:
                item = out_q.get(timeout=0.2)
            except queue.Empty:
                if _stop.is_set():
                    return
                continue
            if item is None:
                return
            pcm, rate = item
            play_pcm(pcm, rate, *targets)
            with backlog_lock:
                backlog["s"] = max(0.0, backlog["s"] - len(pcm) / 2 / rate)

    player = threading.Thread(target=_player, daemon=True)
    player.start()

    while not _stop.is_set():
        try:
            segment = seg_q.get(timeout=0.2)
        except queue.Empty:
            continue

        audio_f32 = segment.astype(np.float32) / 32768.0
        try:
            text = transcribe_segment(whisper, audio_f32, src)
            if not text:
                continue
            translated = do_translate(text, src, tgt)
        except Exception as e:
            # One bad segment must not kill the direction's worker thread
            _emit({"e": "error", "msg": f"pipeline: {type(e).__name__}: {e}"})
            console.print(f"[red]pipeline:[/red] {e}")
            continue
        with _tr_lock:
            _transcripts.append((direction, text, translated))
        _emit({"e": "transcript", "dir": direction, "text": text})
        _emit({"e": "translation", "dir": direction, "text": translated})

        # Streaming TTS: sintetiza próxima frase enquanto atual está tocando
        # Lê piper via ref mutável para suportar hot-swap sem reiniciar Whisper
        sentences = _split_sentences(translated)
        with _piper_lock:
            _cur_piper = _piper_out_ref[0] if direction == "out" else piper

        # Feed OmniVoice the live source audio as reference. One fixed file per
        # direction: the next segment is only processed after playback ends, so
        # it is never overwritten while being read (and no temp files leak).
        if isinstance(_cur_piper, OmniVoiceEngine):
            try:
                import soundfile as _sf
                ref = plat.temp_path(f"ov_live_ref_{direction}.wav")
                _sf.write(ref, segment.astype(np.float32) / 32768.0, SR, subtype="PCM_16")
                _cur_piper.set_live_reference(ref, text)
            except Exception as e:
                console.print(f"[yellow]OmniVoice ref: {e}[/yellow]")
        rate = _cur_piper.config.sample_rate
        # Per-sentence TTS: the first sentence starts playing while the next is synthesized
        for sent in sentences:
            with backlog_lock:
                scale = speech_length_scale(backlog["s"])
            try:
                pcm = b"".join(c.audio_int16_bytes for c in _synthesize(_cur_piper, sent, scale))
            except Exception as e:
                _emit({"e": "error", "msg": f"tts: {type(e).__name__}: {e}"})
                continue
            if pcm:
                with backlog_lock:
                    backlog["s"] += len(pcm) / 2 / rate
                out_q.put((pcm, rate))

    out_q.put(None)
    player.join(timeout=2)


def input_worker(live: Live) -> None:
    while not _stop.is_set():
        try:
            input()
        except EOFError:
            break
        if _ui_state["status"] != "PAUSADO":
            _active.clear()
            _peer_active.clear()
            _ui_state["status"] = "PAUSADO"
        else:
            _active.set()
            _peer_active.set()
            _ui_state["status"] = "TRADUZINDO"
        live.update(build_panel())


# ── Modelos ───────────────────────────────────────────────────────────────────

_ct2_cache: dict[tuple[str, str], tuple] = {}
_ct2_lock = threading.Lock()


def _argos_translator(src: str, tgt: str):
    """(argos Package, ctranslate2.Translator) for an installed pair, cached.

    Bypasses argostranslate.translate, which imports stanza → PyTorch only to
    split sentences (we split with a regex)."""
    key = (src, tgt)
    with _ct2_lock:
        if key in _ct2_cache:
            return _ct2_cache[key]
        import argostranslate.package
        import ctranslate2
        pkg = next((p for p in argostranslate.package.get_installed_packages()
                    if p.from_code == src and p.to_code == tgt), None)
        if pkg is None:
            raise LookupError(f"Argos package {src}->{tgt} is not installed")
        device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        if device == "cuda":
            import praxis_accel
            praxis_accel.ensure_cuda_libs()
        tr = ctranslate2.Translator(str(pkg.package_path / "model"), device=device,
                                    inter_threads=1, intra_threads=0,
                                    # "auto" picks int8 on many CPUs, which turns some
                                    # Argos models (es→en) into garbage loops.
                                    compute_type="default")
        _ct2_cache[key] = (pkg, tr)
        return pkg, tr


ARGOS_BEAM = 4   # argostranslate's default (num_hypotheses=4)
MT_MAX_WORDS = 30          # longer "sentences" are split before translation
MT_MAX_CHARS_NOSPACE = 60  # same limit for scripts without spaces (zh, ja)
_SOFT_BREAK = re.compile(r"(?<=[,;:，、；：])\s*")


def _chunk_for_mt(sentence: str) -> list[str]:
    """Splits an over-long sentence into translatable pieces.

    The translation models degenerate on very long inputs without
    punctuation (found with real speech: a 175-word unpunctuated Italian
    passage came out as "I have not been able to do so…" repeated).
    Pieces are cut at commas/semicolons first, then by length."""
    words = sentence.split()
    spaced = len(words) > 1
    too_long = (len(words) > MT_MAX_WORDS) if spaced else (len(sentence) > MT_MAX_CHARS_NOSPACE)
    if not too_long:
        return [sentence]
    pieces: list[str] = []
    for part in _SOFT_BREAK.split(sentence):
        if not part.strip():
            continue
        if spaced:
            w = part.split()
            for i in range(0, len(w), MT_MAX_WORDS):
                pieces.append(" ".join(w[i:i + MT_MAX_WORDS]))
        else:
            for i in range(0, len(part), MT_MAX_CHARS_NOSPACE):
                pieces.append(part[i:i + MT_MAX_CHARS_NOSPACE])
    # merge tiny pieces back into their neighbour so context isn't lost
    merged: list[str] = []
    for piece in pieces:
        small = len(piece.split()) < 4 if spaced else len(piece) < 8
        if merged and small:
            merged[-1] = f"{merged[-1]} {piece}" if spaced else merged[-1] + piece
        else:
            merged.append(piece)
    return merged


def _translate_pair(text: str, src: str, tgt: str) -> str:
    pkg, tr = _argos_translator(src, tgt)
    sentences = [c for s in _split_sentences(text.strip()) for c in _chunk_for_mt(s)]
    tokens = [pkg.tokenizer.encode(s) for s in sentences]
    prefix = [[pkg.target_prefix]] * len(tokens) if pkg.target_prefix else None
    res = tr.translate_batch(tokens, target_prefix=prefix, replace_unknowns=True,
                             max_batch_size=32, batch_type="tokens",
                             beam_size=ARGOS_BEAM, num_hypotheses=1, length_penalty=0.2)
    out = []
    for r in res:
        v = pkg.tokenizer.decode(r.hypotheses[0])
        if pkg.target_prefix and v.startswith(pkg.target_prefix):
            v = v[len(pkg.target_prefix):]
        out.append(v.strip())
    return " ".join(o for o in out if o)


def _download_argos_pair(src: str, tgt: str) -> None:
    """Baixa e instala um par de tradução Argos."""
    import argostranslate.package, tempfile, requests, base64

    installed = {(p.from_code, p.to_code)
                 for p in argostranslate.package.get_installed_packages()}
    if (src, tgt) in installed:
        return

    console.print(f"[dim]Baixando pacote Argos {src}→{tgt}...[/dim]")

    try:
        r = requests.get(
            "https://api.github.com/repos/argosopentech/argospm-index/contents/index.json",
            timeout=15,
        )
        r.raise_for_status()
        index = json.loads(base64.b64decode(r.json()["content"]).decode())
        entry = next(
            (p for p in index if p.get("from_code") == src and p.get("to_code") == tgt),
            None,
        )
        if entry is None:
            sys.exit(f"[erro] Par {src}→{tgt} não disponível no Argos Translate.")
        url = entry["links"][0]
        dl = requests.get(url, timeout=120, stream=True)
        dl.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".argosmodel", delete=False) as f:
            for chunk in dl.iter_content(65536):
                f.write(chunk)
            tmp_path = f.name
        argostranslate.package.install_from_path(tmp_path)
        import os; os.unlink(tmp_path)
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[yellow]Fallback download padrão: {e}[/yellow]")
        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        pkg = next((p for p in available if p.from_code == src and p.to_code == tgt), None)
        if pkg is None:
            sys.exit(f"[erro] Par {src}→{tgt} não disponível.")
        argostranslate.package.install_from_path(pkg.download())


def setup_argos(src: str, tgt: str) -> None:
    """Instala pares de tradução. Usa inglês como pivot quando o par direto não existe."""
    if src == tgt:
        return
    if src != "en" and tgt != "en":
        _download_argos_pair(src, "en")
        _download_argos_pair("en", tgt)
    else:
        _download_argos_pair(src, tgt)


def do_translate(text: str, src: str, tgt: str) -> str:
    """Traduz texto; pivot automático via inglês quando par direto não existe.
    Translates; pivots through English when there is no direct pair."""
    if src == tgt:
        return text
    if src != "en" and tgt != "en":
        return _translate_pair(_translate_pair(text, src, "en"), "en", tgt)
    return _translate_pair(text, src, tgt)


def load_whisper(model_name: str, device: str | None = None):
    """Loads Whisper on the best backend for this machine (see praxis_accel):
    CUDA (NVIDIA) · MLX (Apple Silicon) · whisper.cpp GPU build · CPU fallback."""
    import praxis_accel as accel

    backend, why = accel.choose_asr(device or os.environ.get("PRAXIS_DEVICE", "auto"))
    console.print(f"[dim]Whisper ({model_name})…[/dim]", end=" ")
    m = accel.load_asr(model_name, backend, log=lambda msg: console.print(f"[yellow]{msg}[/yellow]"))
    used = getattr(m, "backend", backend)
    color = "yellow" if used == "cpu" else "green"
    console.print(f"[{color}]{used.upper()}[/{color}] [dim]({why})[/dim]")
    _emit({"e": "accel", "asr": used, "reason": why})
    return m


class OmniVoiceEngine:
    """Wrapper zero-shot usando k2-fsa/OmniVoice — sem treino, só áudio de referência.
    Zero-shot wrapper using k2-fsa/OmniVoice — no training, just a reference audio clip.

    Interface compatível com PiperVoice / PiperVoice-compatible interface.
    O pipeline passa o áudio fonte atual via set_live_reference() antes da síntese.
    The pipeline passes the live source audio via set_live_reference() before synthesis.
    """

    def __init__(self, wav_path: str):
        self._wav_path = wav_path          # referência fixa (clone gravado) / fixed reference (recorded clone)
        self._model    = None              # carregado na primeira síntese / loaded on first synthesis
        self.config    = type("cfg", (), {"sample_rate": 24000})()
        self._live_ref: str = ""           # live source audio (set per segment)
        self._live_text: str = ""

    def set_live_reference(self, wav_path: str, text: str) -> None:
        """Uses the speaker's current utterance as voice reference."""
        self._live_ref, self._live_text = wav_path, text

    def _load_model(self):
        """Carrega OmniVoice uma vez e mantém em cache. Loads OmniVoice once and caches."""
        if self._model is not None:
            return
        from omnivoice import OmniVoice
        import torch
        import praxis_accel as accel
        device = accel.choose_clone_device()          # cuda · mps (Apple/AMD Mac) · cpu
        dtype  = torch.float16 if device == "cuda" else torch.float32
        self._model = OmniVoice.from_pretrained(
            "k2-fsa/OmniVoice", device_map=device, dtype=dtype)

    def synthesize(self, text: str):
        """Gera áudio com OmniVoice usando áudio de referência e transcrição globais.
        Generates audio with OmniVoice using global reference audio and transcription."""
        self._load_model()

        # Referência: usa áudio fonte capturado pelo pipeline se disponível, senão usa clone fixo
        # Reference: uses source audio captured by pipeline if available, else uses fixed clone
        ref_audio = self._live_ref or self._wav_path
        ref_text  = self._live_text.strip() or "Olá, estou usando o sistema Praxis."

        try:
            audio = self._model.generate(
                text=text,
                ref_audio=ref_audio,
                ref_text=ref_text,
            )
            pcm_f32 = audio[0]  # float32, sr=24000
            pcm_i16 = (np.clip(pcm_f32, -1.0, 1.0) * 32767).astype(np.int16)
        except Exception:
            import traceback
            traceback.print_exc()
            pcm_i16 = np.zeros(100, dtype=np.int16)

        class _Chunk:
            def __init__(self, data):
                self.audio_int16_bytes = data.tobytes()

        yield _Chunk(pcm_i16)


def _has_cuda() -> bool:
    """CUDA availability without importing PyTorch (see OnnxSileroVAD)."""
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def load_piper(path: str):
    """Carrega a voz correta com base no tipo definido no JSON do perfil.
    Loads the correct voice engine based on the type field in the profile JSON.

    Tipos suportados / supported types:
      omnivoice — OmniVoice zero-shot (referência WAV, sem treino)
      (padrão)  — PiperVoice (.onnx, voz genérica)
    """
    if path.endswith(".wav"):
        jp = Path(path).with_suffix(".json")
        if jp.exists():
            meta = json.loads(jp.read_text())
            if meta.get("type") == "omnivoice":
                # OmniVoice zero-shot — usa o WAV do clone como referência fixa
                # OmniVoice zero-shot — uses the clone WAV as fixed reference
                return OmniVoiceEngine(path)
    import praxis_accel as accel
    return accel.load_piper_accelerated(path)


def start_ptt_listener(key_str: str) -> None:
    """Inicia listener pynput para PTT. Formato: 'keyboard:ctrl_r' ou 'mouse:right'."""
    from pynput import keyboard as kb, mouse as ms

    kind, name = key_str.split(":", 1) if ":" in key_str else ("keyboard", key_str)

    if kind == "mouse":
        ptt_btn = getattr(ms.Button, name, None)
        if ptt_btn is None:
            return

        def _on_click(x, y, button, pressed):
            if button != ptt_btn:
                return
            if pressed:
                _active.set()
            else:
                _ptt_flush.set()

        ms.Listener(on_click=_on_click, daemon=True).start()
    else:
        ptt_key = getattr(kb.Key, name, None) or kb.KeyCode.from_char(name)

        def _on_press(key):
            if key == ptt_key:
                _active.set()

        def _on_release(key):
            if key == ptt_key:
                _ptt_flush.set()

        kb.Listener(on_press=_on_press, on_release=_on_release, daemon=True).start()


# ── Main ──────────────────────────────────────────────────────────────────────

def check_environment() -> dict:
    """Smoke check: which optional components are importable + audio backend.

    Used by `praxis.py --check` (CI and support). Never loads models."""
    import importlib.util
    mods = ["numpy", "rich", "sounddevice", "soundfile", "torch", "faster_whisper",
            "argostranslate", "piper", "pynput", "customtkinter", "omnivoice"]
    report: dict = {
        "platform": plat.SYSTEM,
        "python": sys.version.split()[0],
        "modules": {m: importlib.util.find_spec(m) is not None for m in mods},
        "ffmpeg": plat.ffmpeg_exe() is not None,
    }
    try:
        import praxis_accel as accel
        pl = accel.plan()
        report["acceleration"] = {
            "gpus": list(pl.gpus), "asr": pl.asr, "asr_reason": pl.asr_reason,
            "mt": pl.mt_device, "tts_providers": pl.tts_providers or ["CPUExecutionProvider"],
            "clone": pl.clone_device, "cuda_devices": accel.cuda_device_count(),
            "mlx_whisper": accel._has("mlx_whisper"),
            "whispercpp_gpu": accel.whispercpp_gpu_backend(),
        }
    except Exception as e:
        report["acceleration"] = {"error": str(e)}
    try:
        b = _get_backend()
        report["audio_backend"] = b.name
        report["inputs"] = len(b.list_inputs())
        report["outputs"] = len(b.list_outputs())
        report["can_create_virtual_devices"] = b.can_create_virtual_devices
        report["setup_hint"] = b.setup_hint()
    except Exception as e:
        report["audio_backend"] = None
        report["audio_error"] = str(e)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Praxis — tradutor de voz em tempo real")
    parser.add_argument("--src",       default="pt",
                        help="Idioma que você fala (padrão: pt)")
    parser.add_argument("--tgt",       default="en",
                        help="Idioma de saída (padrão: en)")
    parser.add_argument("--voice-out", default=None, dest="voice_out",
                        help="Voz Piper para sua fala traduzida (.onnx) — obrigatório")
    parser.add_argument("--voice-in",  default=None,  dest="voice_in",
                        help="Voz Piper para fala deles traduzida (.onnx) — ativa bilateral")
    parser.add_argument("--model",     default="small",
                        choices=["tiny", "base", "small", "medium",
                                 "large-v2", "large-v3", "large-v3-turbo"])
    parser.add_argument("--mic",    default=None,
                        help="Dispositivo de entrada (veja --list-devices)")
    parser.add_argument("--output", default=None,
                        help="Dispositivo de saída para monitor (veja --list-devices)")
    parser.add_argument("--monitor", action="store_true",
                        help="Tocar tradução na saída selecionada (--output)")
    parser.add_argument("--json-out", action="store_true", dest="json_out",
                        help="Emite eventos JSON para a janela de monitoramento")
    parser.add_argument("--mode", default="vad", choices=["vad", "gate", "ptt"],
                        help="Modo de ativação: vad (automático), gate (threshold RMS), ptt (botão)")
    parser.add_argument("--gate-threshold", type=float, default=0.10, dest="gate_threshold",
                        help="Threshold RMS para modo gate (0.0–1.0, padrão 0.10)")
    parser.add_argument("--ptt-key", default="", dest="ptt_key",
                        help="Tecla/botão PTT. Ex: 'keyboard:ctrl_r', 'mouse:right'")
    parser.add_argument("--list-devices", action="store_true", dest="list_devices",
                        help="Lista dispositivos de áudio e sai")
    parser.add_argument("--check", action="store_true",
                        help="Verifica dependências/áudio (JSON) e sai")
    parser.add_argument("--max-segment", type=float, default=None, dest="max_segment",
                        help=f"Duração máxima de fala sem pausa antes do corte (s, padrão {MAX_SEG_S:g})")
    parser.add_argument("--device", default=None,
                        choices=["auto", "cpu", "cuda", "mlx", "whispercpp"],
                        help="Aceleração do Whisper (padrão: auto / PRAXIS_DEVICE)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.check:
        print(json.dumps(check_environment(), indent=2, ensure_ascii=False))
        return 0
    if args.list_devices:
        b = _get_backend()
        print(f"# backend: {b.name}")
        print("# inputs")
        for dev_id, label in b.list_inputs():
            print(f"{dev_id}\t{label}")
        print("# outputs")
        for dev_id, label in b.list_outputs():
            print(f"{dev_id}\t{label}")
        return 0
    if not args.voice_out:
        parser.error("--voice-out é obrigatório / --voice-out is required")
    if not 0.0 <= args.gate_threshold <= 1.0:
        parser.error("--gate-threshold deve estar entre 0 e 1")
    if args.max_segment is not None:
        if not 2.0 <= args.max_segment <= 30.0:
            parser.error("--max-segment deve estar entre 2 e 30 s")
        global MAX_SEG_S
        MAX_SEG_S = args.max_segment

    global _json_out, console
    _json_out = args.json_out
    if _json_out:
        console = Console(stderr=True)

    bilateral = args.voice_in is not None
    _ui_state.update(src=args.src, tgt=args.tgt, bilateral=bilateral)

    def _shutdown(sig, frame):
        _stop.set()

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    console.rule("[cyan]✦ Praxis[/cyan]")
    try:
        _emit({"e": "progress", "pct": 0, "msg": "Configurando dispositivos…"})
        setup_virtual_devices(bilateral)
        return _run(args, bilateral)
    except SystemExit as e:
        if e.code not in (0, None):
            _emit({"e": "error", "msg": str(e.code)})
        raise
    except Exception as e:
        _emit({"e": "error", "msg": f"{type(e).__name__}: {e}"})
        console.print(f"[red]Erro:[/red] {e}")
        return 1
    finally:
        # Always remove virtual devices, even if startup failed halfway
        teardown_virtual_devices()


def _run(args: argparse.Namespace, bilateral: bool) -> int:
    _emit({"e": "progress", "pct": 20, "msg": "Carregando tradução…"})
    setup_argos(args.src, args.tgt)
    if bilateral:
        setup_argos(args.tgt, args.src)

    _emit({"e": "progress", "pct": 50, "msg": "Carregando Whisper…"})
    whisper   = load_whisper(args.model, args.device)
    _emit({"e": "progress", "pct": 75, "msg": "Carregando voz…"})
    piper_out = load_piper(args.voice_out)
    _piper_out_ref[0] = piper_out
    piper_in  = load_piper(args.voice_in) if bilateral else None
    _emit({"e": "progress", "pct": 95, "msg": "Carregando VAD…"})

    _ui_state["status"] = "TRADUZINDO"

    mic_device     = resolve_mic(args.mic)
    monitor_output = args.output or None

    # PTT: começa inativo, ativa só ao pressionar o botão
    if args.mode == "ptt":
        _active.clear()
        if args.ptt_key:
            start_ptt_listener(args.ptt_key)

    threads: list[threading.Thread] = [
        threading.Thread(target=mic_worker,  args=(mic_device,), daemon=True),
        threading.Thread(target=vad_worker,
                         args=(_out_audio_q, _out_seg_q, args.mode, args.gate_threshold),
                         daemon=True),
        threading.Thread(target=pipeline_worker,
                         args=(_out_seg_q, whisper, piper_out,
                               args.src, args.tgt, "out",
                               args.monitor, monitor_output),
                         daemon=True),
    ]

    if bilateral:
        # The peer is never gated by the user's PTT key — PTT only applies to
        # the user's own microphone, so the peer direction always uses VAD.
        peer_mode = "vad" if args.mode == "ptt" else args.mode
        threads += [
            threading.Thread(target=monitor_worker, daemon=True),
            threading.Thread(target=vad_worker,
                             args=(_in_audio_q, _in_seg_q, peer_mode, args.gate_threshold),
                             kwargs={"active": _peer_active,
                                     "ptt_flush": threading.Event()},
                             daemon=True),
            threading.Thread(target=pipeline_worker,
                             args=(_in_seg_q, whisper, piper_in,
                                   args.tgt, args.src, "in",
                                   False, monitor_output),
                             daemon=True),
        ]

    for t in threads:
        t.start()

    if _json_out:
        _emit({"e": "ready", "mic": _vmic.mic_label, "peer": _vmic.peer_label})

        def _stdin_reader() -> None:
            """Lê comandos JSON do stdin para hot-swap de configurações."""
            for raw in sys.stdin:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    cmd = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if cmd.get("cmd") == "reload_voice":
                    path = cmd.get("path", "")
                    if not path or not Path(path).exists():
                        _emit({"e": "error", "msg": f"voice not found: {path}"})
                        continue
                    try:
                        new_piper = load_piper(path)
                        with _piper_lock:
                            _piper_out_ref[0] = new_piper
                        _emit({"e": "voice_reloaded", "path": path})
                    except Exception as ex:
                        _emit({"e": "error", "msg": str(ex)})
                elif cmd.get("cmd") == "stop":
                    _stop.set()
                    break
            # stdin fechou (UI encerrada) → sinaliza shutdown para teardown limpar os módulos
            _stop.set()

        threading.Thread(target=_stdin_reader, daemon=True).start()

        while not _stop.is_set():
            time.sleep(0.25)
    else:
        with Live(build_panel(), console=console, refresh_per_second=4) as live:
            t_input = threading.Thread(target=input_worker, args=(live,), daemon=True)
            t_input.start()
            while not _stop.is_set():
                live.update(build_panel())
                time.sleep(0.25)

    console.print("[cyan]✦[/cyan] Até mais!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
