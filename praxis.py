#!/usr/bin/env python3
"""Praxis — tradutor de voz em tempo real com microfone virtual (bilateral)."""

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

import numpy as np
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

SR         = 16000
VAD_CHUNK  = 512       # ~32 ms @ 16 kHz
SILENCE_MS = 200       # silêncio para cortar segmento (era 500ms)
MAX_SEG_S  = 4.0       # força corte em falas longas (era 6.0s)
SINK_OUT   = "Praxis_Out"      # null sink → virtual mic outbound
SRC_MIC    = "Praxis_Mic"
SRC_DESC   = "Praxis_Microfone"
SINK_IN    = "Praxis_In"       # null sink → captura audio do interlocutor (bilateral)

_pactl_mods: list[int] = []
_active = threading.Event()
_stop   = threading.Event()
_active.set()

_out_audio_q: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=200)
_in_audio_q:  "queue.Queue[np.ndarray]" = queue.Queue(maxsize=200)
_out_seg_q:   "queue.Queue[np.ndarray]" = queue.Queue()
_in_seg_q:    "queue.Queue[np.ndarray]" = queue.Queue()
_ptt_flush    = threading.Event()   # PTT: sinaliza vad_worker para enviar buffer ao soltar

_transcripts: deque = deque(maxlen=8)
_tr_lock = threading.Lock()
_ui_state: dict = {"status": "INICIANDO", "src": "pt", "tgt": "en", "bilateral": False}
_json_out: bool = False

console = Console()


def _emit(data: dict) -> None:
    if _json_out:
        print(json.dumps(data, ensure_ascii=False), flush=True)


# ── PulseAudio / PipeWire ─────────────────────────────────────────────────────

def _pactl(*args: str) -> str:
    r = subprocess.run(["pactl", *args], capture_output=True, text=True, check=True)
    return r.stdout.strip()


def setup_virtual_devices(bilateral: bool) -> None:
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
    """Toca PCM em um ou mais dispositivos simultaneamente."""
    def _play(dev: str | None) -> None:
        cmd = ["pacat", "--playback", "--format=s16le", f"--rate={rate}", "--channels=1"]
        if dev:
            cmd.append(f"--device={dev}")
        subprocess.run(cmd, input=pcm, check=False)

    targets = [d for d in devices]
    if len(targets) == 1:
        _play(targets[0])
    else:
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
    """Captura microfone via parec (PulseAudio/PipeWire) → _out_audio_q."""
    cmd = ["parec", "--format=s16le", f"--rate={SR}", "--channels=1", "--latency-msec=100"]
    if mic_device:
        cmd.append(f"--device={mic_device}")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    chunk_bytes = VAD_CHUNK * 2  # s16le = 2 bytes por sample
    try:
        while not _stop.is_set():
            if not _active.is_set():
                time.sleep(0.1)
                continue
            data = proc.stdout.read(chunk_bytes)
            if not data:
                break
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
            if not _active.is_set():
                time.sleep(0.1)
                continue
            data = proc.stdout.read(chunk_bytes)
            if not data:
                break
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
    import torch
    from pathlib import Path

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
            while not audio_q.empty():
                try:
                    audio_q.get_nowait()
                except queue.Empty:
                    break
            if speaking:
                _flush_buf()
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
                    _flush_buf()
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
    direction: str,              # "out" | "in"
    monitor: bool = False,
    monitor_output: str | None = None,  # sink de saída para monitor
) -> None:
    """ASR → tradução → TTS streaming por frase → play."""
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

        # Streaming TTS: sintetiza próxima frase enquanto atual está tocando
        sentences = _split_sentences(translated)
        rate      = piper.config.sample_rate
        play_q: "queue.Queue[bytes | None]" = queue.Queue()

        def _synth(sents: list[str]) -> None:
            try:
                for s in sents:
                    pcm = b"".join(c.audio_int16_bytes for c in piper.synthesize(s))
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

    try:
        import argostranslate.translate as _at

        _orig_apply = _at.apply_packaged_translation

        def _safe_apply(pkg, from_code, to_code, input_text):
            try:
                return _orig_apply(pkg, from_code, to_code, input_text)
            except (KeyError, TypeError, AttributeError):
                # Fallback: traduz sentença por sentença sem SBD
                sentences = _regex_split(input_text) or [input_text]
                results = []
                for s in sentences:
                    try:
                        results.append(_orig_apply(pkg, from_code, to_code, s))
                    except Exception:
                        results.append(s)
                return " ".join(results)

        _at.apply_packaged_translation = _safe_apply
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


def load_piper(path: str):
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
