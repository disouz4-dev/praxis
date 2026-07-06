#!/usr/bin/env python3
"""Praxis — tradutor de voz em tempo real com microfone virtual (bilateral).
Real-time voice translator with virtual microphone (bilateral mode).
"""

import argparse
import json
import queue
import re
import signal
import subprocess
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

# ── Constantes de áudio e PulseAudio / Audio and PulseAudio constants ─────────
SR         = 16000          # taxa de amostragem Whisper / Whisper sample rate
VAD_CHUNK  = 512            # ~32 ms @ 16 kHz — janela do VAD / VAD window size
SILENCE_MS = 200            # silêncio para cortar segmento / silence to cut segment
MAX_SEG_S  = 4.0            # força corte em falas longas / max segment length
SINK_OUT   = "Praxis_Out"   # null sink → microfone virtual de saída / outbound virtual mic
SRC_MIC    = "Praxis_Mic"   # nome da fonte de áudio virtual / virtual audio source name
SRC_DESC   = "Praxis_Microfone"  # descrição legível no pavucontrol / human-readable description
SINK_IN    = "Praxis_In"    # null sink → captura áudio do interlocutor / inbound capture sink

# ── Estado global compartilhado entre threads / Global state shared between threads ──
_pactl_mods: list[int] = []     # IDs dos módulos PulseAudio carregados / loaded PulseAudio module IDs
_active = threading.Event()     # sinaliza se tradução está ativa / signals if translation is active
_stop   = threading.Event()     # sinaliza encerramento do programa / signals program shutdown
_active.set()

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
_piper_out_ref: list = [None]   # [PiperVoice | XttsVoice | RvcVoice]
_piper_lock = threading.Lock()

console = Console()


def _emit(data: dict) -> None:
    """Emite evento JSON para o processo pai (UI Electron) quando em modo --json-out.
    Emits JSON event to parent process (Electron UI) when in --json-out mode."""
    if _json_out:
        print(json.dumps(data, ensure_ascii=False), flush=True)


# ── PulseAudio / PipeWire ─────────────────────────────────────────────────────

def _pactl(*args: str) -> str:
    """Executa comando pactl e retorna stdout. / Runs pactl command and returns stdout."""
    r = subprocess.run(["pactl", *args], capture_output=True, text=True, check=True)
    return r.stdout.strip()


def setup_virtual_devices(bilateral: bool) -> None:
    """Cria microfone virtual no PulseAudio/PipeWire.
    Creates virtual microphone in PulseAudio/PipeWire.

    Cria um null sink (SINK_OUT) + remap source (SRC_MIC) para o microfone virtual.
    Em modo bilateral, também cria SINK_IN para capturar áudio do interlocutor.
    Creates a null sink (SINK_OUT) + remap source (SRC_MIC) for the virtual mic.
    In bilateral mode, also creates SINK_IN to capture peer audio.
    """
    mod_sink = int(_pactl(
        "load-module", "module-null-sink",
        f"sink_name={SINK_OUT}",
        f"sink_properties=device.description={SINK_OUT}",
    ))
    mod_src = int(_pactl(
        "load-module", "module-remap-source",
        f"source_name={SRC_MIC}",
        f"master={SINK_OUT}.monitor",
        f"source_properties=device.description={SRC_DESC}",
    ))
    _pactl_mods.extend([mod_sink, mod_src])

    if bilateral:
        mod_in = int(_pactl(
            "load-module", "module-null-sink",
            f"sink_name={SINK_IN}",
            f"sink_properties=device.description=Praxis_Entrada",
        ))
        _pactl_mods.append(mod_in)


def teardown_virtual_devices() -> None:
    """Remove todos os módulos PulseAudio criados pelo Praxis ao encerrar.
    Removes all PulseAudio modules created by Praxis on shutdown."""
    for mod in reversed(_pactl_mods):
        try:
            _pactl("unload-module", str(mod))
        except Exception:
            pass


def resolve_mic(mic_arg: str | None) -> str | None:
    """Se mic_arg termina com :left ou :right, cria um remap source mono e devolve seu nome."""
    if not mic_arg:
        return None
    if not (mic_arg.endswith(":left") or mic_arg.endswith(":right")):
        return mic_arg

    master, side = mic_arg.rsplit(":", 1)
    ch_map   = "front-left"  if side == "left" else "front-right"
    src_name = f"Praxis_Src_{side.capitalize()}"

    mod = int(_pactl(
        "load-module", "module-remap-source",
        f"source_name={src_name}",
        f"master={master}",
        "channels=1",
        f"master_channel_map={ch_map}",
        "channel_map=mono",
        f"source_properties=device.description=Praxis_{side.capitalize()}_Mono",
    ))
    _pactl_mods.append(mod)
    return src_name


def play_pcm(pcm: bytes, rate: int, *devices: str | None) -> None:
    """Toca PCM s16le em um ou mais dispositivos PulseAudio simultaneamente.
    Plays s16le PCM on one or more PulseAudio devices simultaneously."""
    def _play(dev: str | None) -> None:
        cmd = ["pacat", "--playback", "--format=s16le", f"--rate={rate}", "--channels=1"]
        if dev:
            cmd.append(f"--device={dev}")
        subprocess.run(cmd, input=pcm, check=False)

    targets = list(devices)
    if len(targets) == 1:
        _play(targets[0])
    else:
        # Toca em múltiplos dispositivos em paralelo / play on multiple devices in parallel
        ts = [threading.Thread(target=_play, args=(d,), daemon=True) for d in targets]
        for t in ts: t.start()
        for t in ts: t.join()


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

    hints = [f"Mic virtual: [bold]{SRC_DESC}[/bold]"]
    if bilat:
        hints.append(f"Bilateral: redirecione saída deles para [bold]Praxis_Entrada[/bold] (pavucontrol)")
    if bilat:
        hints.append("[dim]Use fone de ouvido para evitar feedback[/dim]")

    return Panel(
        table,
        title="[bold cyan]✦  Praxis[/bold cyan]",
        subtitle=f"[dim]{' │ '.join(hints)}[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
    )


# ── Workers ───────────────────────────────────────────────────────────────────

def mic_worker(mic_device: str | None) -> None:
    """Captura microfone via parec (PulseAudio/PipeWire) → _out_audio_q.

    Sempre drena o pipe mesmo quando inativo — evita acúmulo de áudio antigo
    no buffer do SO que seria liberado na próxima ativação (bug PTT/gate).
    """
    cmd = ["parec", "--format=s16le", f"--rate={SR}", "--channels=1", "--latency-msec=100"]
    if mic_device:
        cmd.append(f"--device={mic_device}")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    chunk_bytes = VAD_CHUNK * 2  # s16le = 2 bytes por sample
    try:
        while not _stop.is_set():
            data = proc.stdout.read(chunk_bytes)
            if not data:
                break
            if not _active.is_set():
                continue  # descarta: drena o pipe mas não enfileira
            arr = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            if len(arr) == VAD_CHUNK:
                try:
                    _out_audio_q.put_nowait(arr.copy())
                except queue.Full:
                    pass
    finally:
        proc.terminate()


def monitor_worker() -> None:
    """Captura Praxis_In.monitor via parec (bilateral — voz do interlocutor)."""
    time.sleep(1.0)
    proc = subprocess.Popen(
        ["parec", f"--device={SINK_IN}.monitor",
         "--format=s16le", f"--rate={SR}", "--channels=1", "--latency-msec=100"],
        stdout=subprocess.PIPE,
    )
    chunk_bytes = VAD_CHUNK * 2
    try:
        while not _stop.is_set():
            data = proc.stdout.read(chunk_bytes)
            if not data:
                break
            if not _active.is_set():
                continue  # descarta: drena o pipe mas não enfileira
            arr = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            if len(arr) == VAD_CHUNK:
                try:
                    _in_audio_q.put_nowait(arr.copy())
                except queue.Full:
                    pass
    finally:
        proc.terminate()


def vad_worker(audio_q:       "queue.Queue[np.ndarray]",
               seg_q:         "queue.Queue[np.ndarray]",
               mode:          str   = "vad",
               gate_threshold: float = 0.10) -> None:
    """Detecta segmentos de fala usando Silero VAD e enfileira em seg_q.
    Detects speech segments using Silero VAD and enqueues them in seg_q.

    Modos / modes:
      vad  — detecção automática por probabilidade de fala / automatic speech probability detection
      gate — threshold RMS simples / simple RMS threshold
      ptt  — push-to-talk via _ptt_flush / push-to-talk via _ptt_flush event
    """
    import torch

    # Carrega Silero VAD local se disponível, senão baixa / load local Silero VAD or download
    _local = Path.home() / ".cache/torch/hub/snakers4_silero-vad_master"
    if _local.exists():
        model, utils = torch.hub.load(str(_local), "silero_vad", source="local",
                                      force_reload=False, onnx=False)
    else:
        model, utils = torch.hub.load("snakers4/silero-vad", "silero_vad",
                                      force_reload=False, onnx=False, trust_repo=True)
    VADIterator = utils[3]
    vad = VADIterator(model, sampling_rate=SR, threshold=0.5,
                      min_silence_duration_ms=SILENCE_MS)

    buf: list[np.ndarray] = []
    speaking = False
    buf_dur  = 0.0
    ptt_mode = (mode == "ptt")

    def _flush_buf() -> None:
        nonlocal buf, buf_dur, speaking
        if buf:
            seg_q.put(np.concatenate(buf))
        buf, buf_dur, speaking = [], 0.0, False
        vad.reset_states()

    while not _stop.is_set():
        # PTT flush: botão solto → envia buffer atual e desativa
        if ptt_mode and _ptt_flush.is_set():
            _ptt_flush.clear()
            _flush_buf()
            _active.clear()

        if not _active.is_set():
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

        ev = vad(torch.from_numpy(chunk), return_seconds=False)
        if ev:
            if "start" in ev and not speaking:
                speaking = True
                buf, buf_dur = [], 0.0
            if "end" in ev and speaking:
                _flush_buf()

        if speaking:
            buf.append((chunk * 32767).clip(-32768, 32767).astype(np.int16))
            buf_dur += VAD_CHUNK / SR
            if buf_dur >= MAX_SEG_S:
                _flush_buf()


_SENT_SPLIT = re.compile(r'(?<=[.!?…])\s+')


def _split_sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]
    return parts or [text]


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

    Sintetiza a próxima frase enquanto a atual está tocando para reduzir latência percebida.
    Synthesizes the next sentence while the current one is playing to reduce perceived latency.
    """
    while not _stop.is_set():
        try:
            segment = seg_q.get(timeout=0.2)
        except queue.Empty:
            continue

        audio_f32 = segment.astype(np.float32) / 32768.0
        segs, info = whisper.transcribe(
            audio_f32, language=src, beam_size=1,
            condition_on_previous_text=False, without_timestamps=True,
            temperature=0,
            no_speech_threshold=0.5,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )
        # Filtra segmentos com alta probabilidade de não-fala
        valid = [s for s in segs if s.no_speech_prob < 0.5]
        text  = " ".join(s.text for s in valid).strip()
        if not text or text in (".", ",", "...", "!"):
            continue

        translated = do_translate(text, src, tgt)
        with _tr_lock:
            _transcripts.append((direction, text, translated))
        _emit({"e": "transcript", "dir": direction, "text": text})
        _emit({"e": "translation", "dir": direction, "text": translated})

        # Alimenta o OmniVoice com o áudio fonte atual como referência (se ativo)
        # Feed OmniVoice with current source audio as reference (if active)
        global _ov_src_audio_path, _ov_src_text
        with _piper_lock:
            _is_ov = isinstance(_piper_out_ref[0] if direction == "out" else piper,
                                 OmniVoiceEngine)
        if _is_ov:
            import soundfile as _sf, tempfile as _tf
            _tmp_ref = _tf.mktemp(suffix=".wav")
            _sf.write(_tmp_ref,
                       segment.astype(np.float32) / 32768.0,
                       16000, subtype="PCM_16")
            _ov_src_audio_path = _tmp_ref
            _ov_src_text = text

        # Streaming TTS: sintetiza próxima frase enquanto atual está tocando
        # Lê piper via ref mutável para suportar hot-swap sem reiniciar Whisper
        sentences = _split_sentences(translated)
        with _piper_lock:
            _cur_piper = _piper_out_ref[0] if direction == "out" else piper
        rate      = _cur_piper.config.sample_rate
        play_q: "queue.Queue[bytes | None]" = queue.Queue()

        def _synth(sents: list[str], _p=_cur_piper) -> None:
            try:
                for s in sents:
                    pcm = b"".join(c.audio_int16_bytes for c in _p.synthesize(s))
                    play_q.put(pcm)
            finally:
                play_q.put(None)

        threading.Thread(target=_synth, args=(sentences,), daemon=True).start()

        while True:
            pcm = play_q.get()
            if pcm is None:
                break
            if direction == "out":
                if monitor:
                    play_pcm(pcm, rate, SINK_OUT, monitor_output)
                else:
                    play_pcm(pcm, rate, SINK_OUT)
            else:
                play_pcm(pcm, rate, monitor_output)


def input_worker(live: Live) -> None:
    while not _stop.is_set():
        try:
            input()
        except EOFError:
            break
        if _active.is_set():
            _active.clear()
            _ui_state["status"] = "PAUSADO"
        else:
            _active.set()
            _ui_state["status"] = "TRADUZINDO"
        live.update(build_panel())


# ── Modelos ───────────────────────────────────────────────────────────────────

def _patch_argos_sbd() -> None:
    """Substitui o sentencizador do argostranslate por regex simples.

    O StanzaSentencizer falha com KeyError 'packages' em recursos stanza
    que não contêm essa chave. Como o objetivo é apenas partir texto em
    sentenças para tradução, um splitter regex é equivalente e mais robusto.
    """
    import re

    def _regex_split(text: str):
        """Divide texto em sentenças por pontuação terminal."""
        parts = re.split(r'(?<=[.!?])\s+', text.strip())
        return [p for p in parts if p]

    try:
        import argostranslate.sbd as _sbd

        _orig_split = _sbd.StanzaSentencizer.split_sentences

        def _safe_split(self, text: str):
            try:
                return _orig_split(self, text)
            except Exception:
                return _regex_split(text)

        _sbd.StanzaSentencizer.split_sentences = _safe_split
    except Exception:
        pass



_patch_argos_sbd()


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
    """Traduz texto; pivot automático via inglês quando par direto não existe."""
    import argostranslate.translate
    if src == tgt:
        return text
    if src != "en" and tgt != "en":
        en_text = argostranslate.translate.translate(text, src, "en")
        return argostranslate.translate.translate(en_text, "en", tgt)
    return argostranslate.translate.translate(text, src, tgt)


def load_whisper(model_name: str):
    from faster_whisper import WhisperModel

    console.print(f"[dim]Whisper ({model_name})...[/dim]", end=" ")
    try:
        m = WhisperModel(model_name, device="cuda", compute_type="int8_float16")
        # Valida GPU com inferência real — cuBLAS é carregado na primeira chamada
        dummy = np.zeros(1600, dtype=np.float32)
        list(m.transcribe(dummy, language="pt")[0])
        console.print("[green]GPU[/green]")
    except Exception:
        m = WhisperModel(model_name, device="cpu", compute_type="int8")
        console.print("[yellow]CPU[/yellow]")
    return m


def _patch_transformers_compat():
    """Monkey-patch para transformers >= 5.x que removeu isin_mps_friendly.
    Monkey-patch for transformers >= 5.x which removed isin_mps_friendly."""
    try:
        import torch
        import transformers.pytorch_utils as _pu
        if not hasattr(_pu, "isin_mps_friendly"):
            _pu.isin_mps_friendly = torch.isin
    except Exception:
        pass


class RvcVoice:
    """Voz clonada via RVC — usa modelo .pth treinado + TTS intermediário para síntese.
    Cloned voice via RVC — uses trained .pth model + intermediate TTS for synthesis.

    Pipeline: texto → Piper TTS (voz genérica) → RVC (.pth) → áudio com voz do usuário
    Pipeline: text → Piper TTS (generic voice) → RVC (.pth) → audio with user's voice
    """

    APPLIO_DIR = "/home/lab2/Documentos/praxis/applio/src"
    PYTHON     = "/home/lab2/Documentos/praxis/applio/venv/bin/python"

    def __init__(self, pth_path: str, sample_rate: int = 40000):
        self._pth_path   = pth_path
        self._index_path = str(Path(pth_path).with_suffix(".index")) if Path(
            pth_path).with_suffix(".index").exists() else ""
        self.config = type("cfg", (), {"sample_rate": sample_rate})()

    def synthesize(self, text: str):
        """Síntese em 2 etapas: TTS genérico → conversão de voz RVC.
        Two-step synthesis: generic TTS → RVC voice conversion."""
        import subprocess, tempfile, os, wave as _wave
        import numpy as _np

        # Passo 1: gera áudio com voz genérica usando edge-tts (rápido, sem GPU)
        # Step 1: generate audio with generic voice using edge-tts (fast, no GPU)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_mp3 = f.name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_tts = f.name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_out = f.name

        try:
            # Edge-TTS: gera voz genérica PT-BR / generates generic PT-BR voice
            subprocess.run([
                "edge-tts", "--voice", "pt-BR-AntonioNeural",
                "--text", text, "--write-media", tmp_mp3
            ], check=True, capture_output=True)

            # Converte MP3 para WAV mono 40kHz / convert MP3 to WAV mono 40kHz
            subprocess.run([
                "ffmpeg", "-y", "-i", tmp_mp3,
                "-ar", "40000", "-ac", "1", tmp_tts
            ], check=True, capture_output=True)

            # Passo 2: RVC — converte voz genérica para voz do usuário
            # Step 2: RVC — convert generic voice to user's voice
            infer_script = Path(self.APPLIO_DIR) / "rvc" / "infer" / "infer.py"
            subprocess.run([
                self.PYTHON, str(infer_script),
                "0",              # pitch shift semitones
                "0.75",           # index rate
                "0",              # gpu index
                "0.25",           # protect
                "rmvpe",          # f0 method
                tmp_tts,          # input wav
                tmp_out,          # output wav
                self._pth_path,   # model .pth
                self._index_path if self._index_path else "",
                "wav",            # export format
                "contentvec",     # embedder model
            ], check=True, capture_output=True, cwd=self.APPLIO_DIR)

            # Lê o WAV gerado e devolve como chunk compatível com PiperVoice
            # Read generated WAV and return as PiperVoice-compatible chunk
            with _wave.open(tmp_out, "rb") as wf:
                raw = wf.readframes(wf.getnframes())
                self.config = type("cfg", (), {"sample_rate": wf.getframerate()})()
            pcm = _np.frombuffer(raw, dtype=_np.int16)

        finally:
            for p in (tmp_mp3, tmp_tts, tmp_out):
                try:
                    os.unlink(p)
                except Exception:
                    pass

        class _Chunk:
            def __init__(self, data):
                self.audio_int16_bytes = data.tobytes()

        yield _Chunk(pcm)


class XttsVoice:
    """Wrapper que imita a interface do PiperVoice usando XTTS v2 (Coqui TTS).
    Wrapper mimicking PiperVoice interface using XTTS v2 (Coqui TTS).
    Usado como fallback quando o modelo RVC ainda não foi treinado.
    Used as fallback when the RVC model hasn't been trained yet.
    """

    _MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"

    def __init__(self, wav_path: str, lang: str = "pt"):
        _patch_transformers_compat()
        from TTS.api import TTS
        device = "cuda" if _has_cuda() else "cpu"
        self._tts     = TTS(self._MODEL_NAME).to(device)
        self._wav_path = wav_path
        self._lang     = lang
        self.config    = type("cfg", (), {"sample_rate": 24000})()

    def synthesize(self, text: str):
        """Gera áudio e retorna iterador de chunks com .audio_int16_bytes."""
        import numpy as np, tempfile, os, wave as _wave
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name
        try:
            self._tts.tts_to_file(
                text=text,
                speaker_wav=self._wav_path,
                language=self._lang,
                file_path=tmp,
            )
            with _wave.open(tmp, "rb") as wf:
                raw = wf.readframes(wf.getnframes())
            pcm = np.frombuffer(raw, dtype=np.int16)
        finally:
            os.unlink(tmp)

        class _Chunk:
            def __init__(self, data):
                self.audio_int16_bytes = data.tobytes()

        yield _Chunk(pcm)


class OmniVoiceEngine:
    """Wrapper zero-shot usando k2-fsa/OmniVoice — sem treino, só áudio de referência.
    Zero-shot wrapper using k2-fsa/OmniVoice — no training, just a reference audio clip.

    Interface compatível com PiperVoice / PiperVoice-compatible interface.
    Usa globals _ov_src_audio_path e _ov_src_text definidos pelo pipeline antes da síntese.
    Uses globals _ov_src_audio_path and _ov_src_text set by the pipeline before synthesis.
    """

    def __init__(self, wav_path: str):
        self._wav_path = wav_path          # referência fixa (clone gravado) / fixed reference (recorded clone)
        self._model    = None              # carregado na primeira síntese / loaded on first synthesis
        self.config    = type("cfg", (), {"sample_rate": 24000})()

    def _load_model(self):
        """Carrega OmniVoice uma vez e mantém em cache. Loads OmniVoice once and caches."""
        if self._model is not None:
            return
        from omnivoice import OmniVoice
        import torch
        device = "cuda" if _has_cuda() else "cpu"
        dtype  = torch.float16 if device == "cuda" else torch.float32
        self._model = OmniVoice.from_pretrained(
            "k2-fsa/OmniVoice", device_map=device, dtype=dtype)

    def synthesize(self, text: str):
        """Gera áudio com OmniVoice usando áudio de referência e transcrição globais.
        Generates audio with OmniVoice using global reference audio and transcription."""
        import numpy as np
        import soundfile as sf, tempfile, os

        self._load_model()

        # Referência: usa áudio fonte capturado pelo pipeline se disponível, senão usa clone fixo
        # Reference: uses source audio captured by pipeline if available, else uses fixed clone
        ref_audio = _ov_src_audio_path or self._wav_path
        ref_text  = _ov_src_text.strip() or "Olá, estou usando o sistema Praxis."

        try:
            audio = self._model.generate(
                text=text,
                ref_audio=ref_audio,
                ref_text=ref_text,
            )
            pcm_f32 = audio[0]  # float32, sr=24000
            pcm_i16 = (np.clip(pcm_f32, -1.0, 1.0) * 32767).astype(np.int16)
        except Exception:
            import traceback; traceback.print_exc()
            pcm_i16 = np.zeros(100, dtype=np.int16)

        class _Chunk:
            def __init__(self, data):
                self.audio_int16_bytes = data.tobytes()

        yield _Chunk(pcm_i16)


# Globals do pipeline: áudio fonte atual + transcrição para referência do OmniVoice
# Pipeline globals: current source audio + transcription for OmniVoice reference
_ov_src_audio_path: str = ""   # caminho para WAV do áudio fonte / path to source audio WAV
_ov_src_text:       str = ""   # transcrição do áudio fonte / source audio transcription


def _has_cuda() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


def load_piper(path: str):
    """Carrega a voz correta com base no tipo definido no JSON do perfil.
    Loads the correct voice engine based on the type field in the profile JSON.

    Tipos suportados / supported types:
      xtts / chatterbox — XTTS v2 (zero-shot, sem treino)
      rvc               — RVC + modelo .pth treinado (alta fidelidade)
      (padrão)          — PiperVoice (.onnx, voz genérica)
    """
    if path.endswith(".wav"):
        jp = Path(path).with_suffix(".json")
        if jp.exists():
            meta = json.loads(jp.read_text())
            voice_type = meta.get("type", "")
            if voice_type == "rvc":
                # Modelo RVC treinado — usa .pth gerado pelo pipeline de treino
                # Trained RVC model — uses .pth generated by training pipeline
                pth_path = str(Path(path).parent / meta.get("pth", ""))
                if Path(pth_path).exists():
                    return RvcVoice(pth_path)
                # Fallback para XTTS se .pth não existe ainda
                # Fallback to XTTS if .pth doesn't exist yet
            if voice_type == "omnivoice":
                # OmniVoice zero-shot — usa o WAV do clone como referência fixa
                # OmniVoice zero-shot — uses the clone WAV as fixed reference
                return OmniVoiceEngine(path)
            if voice_type in ("chatterbox", "xtts", "rvc"):
                lang = meta.get("lang", "pt")
                return XttsVoice(path, lang)
    from piper import PiperVoice
    return PiperVoice.load(path)


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

def main() -> None:
    parser = argparse.ArgumentParser(description="Praxis — tradutor de voz em tempo real")
    parser.add_argument("--src",       default="pt",
                        help="Idioma que você fala (padrão: pt)")
    parser.add_argument("--tgt",       default="en",
                        help="Idioma de saída (padrão: en)")
    parser.add_argument("--voice-out", required=True, dest="voice_out",
                        help="Voz Piper para sua fala traduzida (.onnx)")
    parser.add_argument("--voice-in",  default=None,  dest="voice_in",
                        help="Voz Piper para fala deles traduzida (.onnx) — ativa bilateral")
    parser.add_argument("--model",     default="small",
                        choices=["tiny", "base", "small", "medium", "large-v2"])
    parser.add_argument("--mic",    default=None,
                        help="Nome da fonte de áudio (pactl list short sources)")
    parser.add_argument("--output", default=None,
                        help="Nome do sink de saída para monitor (pactl list short sinks)")
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
    args = parser.parse_args()

    global _json_out, console
    _json_out = args.json_out
    if _json_out:
        console = Console(stderr=True)

    bilateral = args.voice_in is not None
    _ui_state.update(src=args.src, tgt=args.tgt, bilateral=bilateral)

    console.rule("[cyan]✦ Praxis[/cyan]")
    _emit({"e": "progress", "pct": 0, "msg": "Configurando dispositivos…"})
    setup_virtual_devices(bilateral)

    def _shutdown(sig, frame):
        _stop.set()

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    _emit({"e": "progress", "pct": 20, "msg": "Carregando tradução…"})
    setup_argos(args.src, args.tgt)
    if bilateral:
        setup_argos(args.tgt, args.src)

    _emit({"e": "progress", "pct": 50, "msg": "Carregando Whisper…"})
    whisper   = load_whisper(args.model)
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
        threads += [
            threading.Thread(target=monitor_worker, daemon=True),
            threading.Thread(target=vad_worker,
                             args=(_in_audio_q, _in_seg_q, args.mode, args.gate_threshold),
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
        _emit({"e": "ready"})

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
                    if path and Path(path).exists():
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

    teardown_virtual_devices()
    console.print("[cyan]✦[/cyan] Até mais!")


if __name__ == "__main__":
    main()
