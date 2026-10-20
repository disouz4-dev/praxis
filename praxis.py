#!/usr/bin/env python3
"""Praxis — tradutor de voz em tempo real com microfone virtual (modo bilateral)."""

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

# ── Constantes de áudio e PulseAudio ──────────────────────────────────────────
SR         = 16000          # taxa de amostragem do Whisper
VAD_CHUNK  = 512            # ~32 ms a 16 kHz — janela do detector de fala
SILENCE_MS = 200            # silêncio que encerra um trecho de fala
MAX_SEG_S  = 6.0            # corte em falas longas sem pausa (duração máxima do trecho)
                            # (medido: 4 s → pt 20,5% de taxa de erro de palavras, 6 s → 16,7%, 8 s → 14,3%)
PREROLL_S  = 0.25           # áudio guardado de antes do detector de fala disparar (início da fala)
MIN_SEG_S  = 0.8            # pedaços menores são juntados ao próximo trecho
CARRY_MAX_WAIT_S = 1.0      # …mas saem sozinhos após 1 s de silêncio ("Sim." não fica preso)
SMART_CUT_WINDOW_S = 1.5    # trecho longo é cortado no ponto mais silencioso deste final
SINK_OUT   = plat.SINK_OUT  # saída nula → microfone virtual de saída
SRC_MIC    = plat.SRC_MIC   # nome da fonte de áudio virtual
SRC_DESC   = plat.SRC_DESC  # descrição legível no pavucontrol
SINK_IN    = plat.SINK_IN   # saída nula → captura o áudio do interlocutor

# ── Estado global compartilhado entre threads ──
_active = threading.Event()     # sinaliza se a tradução está ativa
_peer_active = threading.Event()  # direção do interlocutor: segue pausar/retomar, mas nunca o botão de falar
_stop   = threading.Event()     # sinaliza o encerramento do programa
_active.set()
_peer_active.set()

# Backend de áudio da plataforma + dispositivos virtuais (definidos em main)
_backend: "plat.AudioBackend | None" = None
_vmic: "plat.VirtualMic" = plat.VirtualMic(target=SINK_OUT, mic_label=SRC_DESC)

# Filas de áudio bruto (blocos do detector de fala)
_out_audio_q: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=200)  # microfone do usuário
_in_audio_q:  "queue.Queue[np.ndarray]" = queue.Queue(maxsize=200)  # áudio do interlocutor

# Filas de trechos de fala detectados
_out_seg_q:   "queue.Queue[np.ndarray]" = queue.Queue()
_in_seg_q:    "queue.Queue[np.ndarray]" = queue.Queue()

# PTT (aperte para falar): avisa o detector de fala para enviar o buffer ao soltar o botão
_ptt_flush    = threading.Event()

# Histórico de transcrições para a interface de terminal
_transcripts: deque = deque(maxlen=8)
_tr_lock = threading.Lock()
_ui_state: dict = {"status": "INICIANDO", "src": "pt", "tgt": "en", "bilateral": False}
_json_out: bool = False  # modo JSON para integração com a interface gráfica

# Referência mutável para trocar a voz sem reiniciar o Whisper
_piper_out_ref: list = [None]   # [PiperVoice | OmniVoiceEngine]
_piper_lock = threading.Lock()

console = Console()


def _emit(data: dict) -> None:
    """Emite evento JSON para o processo pai (interface gráfica) quando em modo --json-out."""
    if _json_out:
        print(json.dumps(data, ensure_ascii=False), flush=True)


# ── Áudio (delegado ao praxis_platform) ──────────────────────────────────────

def _get_backend() -> "plat.AudioBackend":
    global _backend
    if _backend is None:
        _backend = plat.get_backend()
    return _backend


def setup_virtual_devices(bilateral: bool) -> "plat.VirtualMic":
    """Cria (Linux) ou localiza (macOS/Windows) o microfone virtual."""
    global _vmic
    _vmic = _get_backend().setup_virtual_mic(bilateral)
    return _vmic


def teardown_virtual_devices() -> None:
    """Remove os dispositivos virtuais criados pelo Praxis (não faz nada onde nada foi criado)."""
    if _backend is not None:
        _backend.teardown()


def resolve_mic(mic_arg: str | None) -> str | None:
    """Linux: 'dev:left/right' → fonte mono remapeada. Nos outros sistemas o canal
    é escolhido na captura, então o id volta inalterado."""
    return _get_backend().resolve_mic(mic_arg)


def play_pcm(pcm: bytes, rate: int, *devices: str | None) -> None:
    """Toca PCM s16le mono em um ou mais dispositivos ao mesmo tempo."""
    _get_backend().play_pcm_multi(pcm, rate, devices)


# ── Interface de terminal ─────────────────────────────────────────────────────

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


# ── Threads de trabalho ───────────────────────────────────────────────────────

def capture_worker(device: str | None,
                   audio_q: "queue.Queue[np.ndarray]",
                   active: threading.Event,
                   delay: float = 0.0) -> None:
    """Captura áudio mono 16 kHz de `device` → audio_q (blocos de VAD_CHUNK amostras).

    Sempre drena a captura mesmo quando inativo — evita acúmulo de áudio antigo
    no buffer do sistema, que seria liberado na próxima ativação (bug PTT/gate).
    """
    if delay:
        time.sleep(delay)
    try:
        cap = _get_backend().open_capture(device, SR, VAD_CHUNK)
    except Exception as e:
        _emit({"e": "error", "msg": f"falha na captura de áudio ({device or 'padrão'}): {e}"})
        console.print(f"[red]Captura de áudio falhou:[/red] {e}")
        return
    try:
        while not _stop.is_set():
            data = cap.read()
            if not data:
                break
            if not active.is_set():
                continue  # descarta: drena, mas não enfileira
            arr = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            if len(arr) == VAD_CHUNK:
                try:
                    audio_q.put_nowait(arr.copy())
                except queue.Full:
                    pass
    finally:
        cap.close()


def mic_worker(mic_device: str | None) -> None:
    """Microfone do usuário → _out_audio_q."""
    capture_worker(mic_device, _out_audio_q, _active)


def monitor_worker() -> None:
    """Áudio do interlocutor (bilateral) → _in_audio_q."""
    capture_worker(_vmic.peer_capture, _in_audio_q, _peer_active, delay=1.0)


class OnnxSileroVAD:
    """Detector de fala Silero contínuo sobre onnxruntime — mesma API do VADIterator do silero.

    Usa o modelo Silero v6 em ONNX que acompanha o faster-whisper, então o motor
    não precisa do PyTorch. (PyTorch + CTranslate2 no mesmo processo carregam duas
    bibliotecas OpenMP e derrubam o Whisper no macOS.)"""

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
    """→ (modelo, fábrica compatível com VADIterator). Usa ONNX (sem torch) quando possível."""
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
    """Detecta trechos de fala com o detector Silero e os enfileira em seg_q.

    Modos:
      vad  — detecção automática pela probabilidade de fala
      gate — limiar simples de volume (RMS)
      ptt  — aperte para falar, via _ptt_flush

    Qualidade dos trechos (medida com benchmarks/run_benchmarks.py asr):
      * pré-gravação — o detector dispara um ou dois blocos *depois* do início
        da fala; os últimos PREROLL_S de áudio são colocados antes, para a
        primeira sílaba não se perder.
      * corte inteligente — fala longa é cortada no bloco mais silencioso dos
        últimos SMART_CUT_WINDOW_S, em vez de no meio da palavra, sem reiniciar
        o detector.
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
        """Envia um trecho longo, mas continua ouvindo (a fala continua)."""
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

    carry: list[np.ndarray] = []       # sobra pequena após um corte, colada ao próximo trecho
    carry_age = 0                      # blocos em silêncio desde que a sobra foi guardada

    def _emit_seg(chunks: list[np.ndarray], force: bool = False) -> None:
        nonlocal carry, carry_age
        chunks = carry + chunks
        carry, carry_age = [], 0
        if not chunks:
            return
        if not force and len(chunks) * chunk_s < MIN_SEG_S:
            # Curto demais para o Whisper sozinho (ele não devolve nada e a
            # sílaba se perde) — guarda para o próximo trecho.
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
        # PTT: botão solto → envia o buffer atual e desativa
        if ptt_mode and ptt_flush.is_set():
            ptt_flush.clear()
            _flush_buf(force=True)             # botão solto: envia tudo agora
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

        # Modo gate: ignora blocos abaixo do limiar de volume (RMS)
        if mode == "gate":
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            if rms < gate_threshold:
                if speaking:
                    _flush_buf()   # envia fala já capturada acima do gate
                else:
                    vad.reset_states()  # sem fala: limpa o estado do detector para não vazar
                continue

        i16 = (chunk * 32767).clip(-32768, 32767).astype(np.int16)
        ev = vad(chunk, return_seconds=False)
        if ev and "start" in ev and not speaking:
            speaking = True
            buf = list(preroll)                 # início da fala, anterior ao disparo
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
                    _emit_seg([], force=True)   # fala curta seguida de silêncio

        if ev and "end" in ev and speaking:
            _flush_buf()
        elif speaking and buf_dur >= max_seg_s:
            _cut_long()


_SENT_SPLIT = re.compile(r'(?<=[.!?…])\s+')

# Parâmetros de decodificação do Whisper usados em produção
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
NO_SPEECH_DROP = 0.6       # no_speech_threshold padrão do Whisper
LOGPROB_DROP = -1.0        # … combinado com baixa confiança no texto decodificado


def collapse_repetitions(text: str, max_repeats: int = 2) -> str:
    """Remove os laços de alucinação do Whisper ("o que é o que é o que é …").

    Qualquer frase de 1 a 8 palavras repetida em sequência mais de `max_repeats`
    vezes é mantida só `max_repeats` vezes."""
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


_opencc = None


def _to_simplified(text: str) -> str:
    """O Whisper às vezes escreve chinês com caracteres tradicionais (學生) em vez
    dos simplificados (学生): a mesma palavra, que o tradutor e a voz tratam pior.
    Converte para simplificado quando a biblioteca opencc está instalada."""
    global _opencc
    try:
        if _opencc is None:
            from opencc import OpenCC
            _opencc = OpenCC("t2s")
        return _opencc.convert(text)
    except Exception:
        return text


# Contexto entre trechos: o fim do que já foi transcrito vai como "dica" para o
# Whisper (nomes, assunto, grafia). Desligado até a medição provar que ajuda.
USE_CONTEXT = os.environ.get("PRAXIS_CONTEXTO", "") == "1"
CONTEXT_CHARS = 200


def transcribe_segment(whisper, audio_f32: np.ndarray, lang: str, prompt: str | None = None) -> str:
    """Reconhecimento de fala de um trecho (float32, 16 kHz) → texto ('' = sem fala).

    Compartilhado pelo pipeline ao vivo e pelos benchmarks, para que ambos meçam o mesmo código."""
    opts = dict(WHISPER_OPTS)
    if prompt:
        opts["initial_prompt"] = prompt[-CONTEXT_CHARS:]
    segs, _info = whisper.transcribe(audio_f32, language=lang, **opts)
    # Descarta um trecho só quando o Whisper acha que não é fala E está inseguro
    # do texto (a regra do próprio Whisper). Filtrar só por no_speech_prob jogava
    # fora fala transcrita corretamente (medido: 0,53–0,59 em frases reais).
    text = " ".join(s.text for s in segs
                    if not (s.no_speech_prob > NO_SPEECH_DROP
                            and getattr(s, "avg_logprob", 0.0) < LOGPROB_DROP)).strip()
    # O Whisper pode partir um caractere de vários bytes entre tokens (visto em hindi):
    # nunca repassar o "�" resultante para a tradução e a fala.
    text = re.sub(r"\s{2,}", " ", text.replace("\ufffd", "")).strip()
    if lang == "zh":
        text = _to_simplified(text)
    text = collapse_repetitions(text)
    return "" if text in _NOISE_ONLY else text


def _split_sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]
    return parts or [text]


# Velocidade de fala adaptativa: quando a fala traduzida se acumula (idiomas cuja
# tradução é mais longa que o original — ex.: en→ar medido em 121%), a voz fala
# mais rápido para alcançar, em vez de ficar cada vez mais atrasada.
RATE_STEPS = ((1.5, 1.0), (4.0, 0.87), (8.0, 0.77), (float("inf"), 0.7))   # (atraso ≤ s, length_scale)


def speech_length_scale(backlog_s: float) -> float:
    """length_scale do Piper para o atraso de reprodução atual (1.0 = velocidade normal)."""
    for limit, scale in RATE_STEPS:
        if backlog_s <= limit:
            return scale
    return RATE_STEPS[-1][1]


def _synthesize(voice, text: str, length_scale: float):
    """Síntese de voz numa velocidade dada; vozes sem controle de velocidade
    (OmniVoice, dublês de teste) usam a velocidade normal. A calibração própria
    da voz (praxis_rate_scale, para vozes lentas) é aplicada por cima."""
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
    direction: str,              # "out" (usuário) | "in" (interlocutor)
    monitor: bool = False,
    monitor_output: str | None = None,
) -> None:
    """Pipeline completo: reconhecimento de fala (Whisper) → tradução (Argos) →
    síntese de voz frase a frase → reprodução.

    O áudio traduzido toca numa thread própria (em ordem, sem sobreposição):
    enquanto uma frase é falada, o Whisper já transcreve o próximo trecho.
    Medido com benchmarks/stream_test.py: no desenho serial antigo
    (reconhecimento → tradução → síntese → esperar a reprodução → próximo), um
    processador rodando `small` ficava cada vez mais atrasado em fala contínua
    (atraso de +38…+94 ms por segundo).
    """
    if direction == "out":
        targets = (_vmic.target, monitor_output) if monitor else (_vmic.target,)
    else:
        targets = (monitor_output,)
    out_q: "queue.Queue[tuple[bytes, int] | None]" = queue.Queue()
    backlog = {"s": 0.0}                      # segundos de fala traduzida ainda não tocados
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

    context = ""                                   # o que já foi dito nesta direção
    while not _stop.is_set():
        try:
            segment = seg_q.get(timeout=0.2)
        except queue.Empty:
            continue

        audio_f32 = segment.astype(np.float32) / 32768.0
        try:
            if USE_CONTEXT:
                text = transcribe_segment(whisper, audio_f32, src, prompt=context or None)
                if text:
                    context = (context + " " + text)[-CONTEXT_CHARS * 2:]
            else:
                text = transcribe_segment(whisper, audio_f32, src)
            if not text:
                continue
            translated = do_translate(text, src, tgt)
        except Exception as e:
            # Um trecho com problema não pode derrubar a thread desta direção
            _emit({"e": "error", "msg": f"pipeline: {type(e).__name__}: {e}"})
            console.print(f"[red]pipeline:[/red] {e}")
            continue
        with _tr_lock:
            _transcripts.append((direction, text, translated))
        _emit({"e": "transcript", "dir": direction, "text": text})
        _emit({"e": "translation", "dir": direction, "text": translated})

        # Síntese contínua: sintetiza a próxima frase enquanto a atual está tocando
        # Lê a voz pela referência mutável para permitir troca sem reiniciar o Whisper
        sentences = _split_sentences(translated)
        with _piper_lock:
            _cur_piper = _piper_out_ref[0] if direction == "out" else piper

        # Passa ao OmniVoice o áudio original ao vivo como referência. Um arquivo
        # fixo por direção: o próximo trecho só é processado depois que a
        # reprodução termina, então nunca é sobrescrito durante a leitura (e não
        # sobram arquivos temporários).
        if isinstance(_cur_piper, OmniVoiceEngine):
            try:
                import soundfile as _sf
                ref = plat.temp_path(f"ov_live_ref_{direction}.wav")
                _sf.write(ref, segment.astype(np.float32) / 32768.0, SR, subtype="PCM_16")
                _cur_piper.set_live_reference(ref, text)
            except Exception as e:
                console.print(f"[yellow]OmniVoice ref: {e}[/yellow]")
        rate = _cur_piper.config.sample_rate
        # Síntese por frase: a primeira frase começa a tocar enquanto a próxima é sintetizada
        for sent in sentences:
            with backlog_lock:
                scale = speech_length_scale(backlog["s"])
            try:
                pcm = b"".join(c.audio_int16_bytes for c in _synthesize(_cur_piper, sent, scale))
            except Exception as e:
                _emit({"e": "error", "msg": f"síntese de voz: {type(e).__name__}: {e}"})
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
    """(Package do argos, ctranslate2.Translator) de um par instalado, em cache.

    Evita argostranslate.translate, que importa stanza → PyTorch só para
    dividir frases (aqui dividimos com uma expressão regular)."""
    key = (src, tgt)
    with _ct2_lock:
        if key in _ct2_cache:
            return _ct2_cache[key]
        import argostranslate.package
        import ctranslate2
        pkg = next((p for p in argostranslate.package.get_installed_packages()
                    if p.from_code == src and p.to_code == tgt), None)
        if pkg is None:
            raise LookupError(f"Pacote Argos {src}->{tgt} não está instalado")
        device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        if device == "cuda":
            import praxis_accel
            praxis_accel.ensure_cuda_libs()
        tr = ctranslate2.Translator(str(pkg.package_path / "model"), device=device,
                                    inter_threads=1, intra_threads=0,
                                    # "auto" escolhe int8 em muitos processadores, o que faz
                                    # alguns modelos Argos (es→en) gerarem lixo repetido.
                                    compute_type="default")
        _ct2_cache[key] = (pkg, tr)
        return pkg, tr


ARGOS_BEAM = 4   # padrão do argostranslate (num_hypotheses=4)
MT_MAX_WORDS = 30          # "frases" mais longas são divididas antes da tradução
MT_MAX_CHARS_NOSPACE = 60  # mesmo limite para escritas sem espaços (zh, ja)
_SOFT_BREAK = re.compile(r"(?<=[,;:，、；：])\s*")


def _chunk_for_mt(sentence: str) -> list[str]:
    """Divide uma frase longa demais em pedaços traduzíveis.

    Os modelos de tradução degeneram com entradas muito longas sem
    pontuação (achado com fala real: um trecho de 175 palavras em italiano,
    sem pontuação, saiu como "I have not been able to do so…" repetido).
    Os pedaços são cortados primeiro em vírgulas/ponto e vírgula, depois por tamanho."""
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
    # junta pedaços minúsculos ao vizinho para não perder o contexto
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


def _install_argos_package(path) -> None:
    """Instala um pacote do Argos (.argosmodel, que é um zip) extraindo-o na pasta
    de pacotes. Não usa install_from_path: depois de extrair, ela importa
    argostranslate.translate → stanza → PyTorch, que o Praxis não instala, e a
    primeira instalação de japonês/coreano falhava com "No module named 'stanza'"."""
    import zipfile
    import argostranslate.settings
    if not zipfile.is_zipfile(path):
        raise ValueError(f"pacote de tradução inválido (não é um arquivo zip): {path}")
    with zipfile.ZipFile(path) as zf:
        zf.extractall(path=argostranslate.settings.package_data_dir)


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
        _install_argos_package(tmp_path)
        import os; os.unlink(tmp_path)
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[yellow]Usando o download padrão como alternativa: {e}[/yellow]")
        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        pkg = next((p for p in available if p.from_code == src and p.to_code == tgt), None)
        if pkg is None:
            sys.exit(f"[erro] Par {src}→{tgt} não disponível.")
        _install_argos_package(pkg.download())


def setup_argos(src: str, tgt: str) -> None:
    """Instala pares de tradução. Usa o inglês como intermediário quando o par direto não existe."""
    if src == tgt:
        return
    if src != "en" and tgt != "en":
        _download_argos_pair(src, "en")
        _download_argos_pair("en", tgt)
    else:
        _download_argos_pair(src, tgt)


def do_translate(text: str, src: str, tgt: str) -> str:
    """Traduz texto; passa pelo inglês automaticamente quando não existe o par direto."""
    if src == tgt:
        return text
    if src != "en" and tgt != "en":
        return _translate_pair(_translate_pair(text, src, "en"), "en", tgt)
    return _translate_pair(text, src, tgt)


def load_whisper(model_name: str, device: str | None = None):
    """Carrega o Whisper no melhor backend para esta máquina (veja praxis_accel):
    CUDA (NVIDIA) · MLX (Apple Silicon) · whisper.cpp com placa de vídeo · processador como reserva."""
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
    """Adaptador zero-shot usando k2-fsa/OmniVoice — sem treino, só um áudio de referência.

    Interface compatível com PiperVoice.
    O pipeline passa o áudio original atual via set_live_reference() antes da síntese.
    """

    def __init__(self, wav_path: str):
        self._wav_path = wav_path          # referência fixa (clone gravado)
        self._model    = None              # carregado na primeira síntese
        self.config    = type("cfg", (), {"sample_rate": 24000})()
        self._live_ref: str = ""           # áudio original ao vivo (definido a cada trecho)
        self._live_text: str = ""

    def set_live_reference(self, wav_path: str, text: str) -> None:
        """Usa a fala atual de quem está falando como referência de voz."""
        self._live_ref, self._live_text = wav_path, text

    def _load_model(self):
        """Carrega o OmniVoice uma vez e mantém em cache."""
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
        """Gera áudio com OmniVoice usando o áudio de referência e a transcrição."""
        self._load_model()

        # Referência: usa o áudio original capturado pelo pipeline se houver; senão, o clone fixo
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
    """Disponibilidade de CUDA sem importar o PyTorch (veja OnnxSileroVAD)."""
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def load_piper(path: str):
    """Carrega a voz correta com base no tipo definido no JSON do perfil.

    Tipos suportados:
      omnivoice — OmniVoice zero-shot (referência WAV, sem treino)
      (padrão)  — PiperVoice (.onnx, voz genérica)
    """
    if path.endswith(".wav"):
        jp = Path(path).with_suffix(".json")
        if jp.exists():
            meta = json.loads(jp.read_text())
            if meta.get("type") == "omnivoice":
                # OmniVoice zero-shot — usa o WAV do clone como referência fixa
                return OmniVoiceEngine(path)
    import praxis_accel as accel
    return accel.load_piper_accelerated(path)


def start_ptt_listener(key_str: str) -> None:
    """Inicia o ouvinte pynput para o PTT. Formato: 'keyboard:ctrl_r' ou 'mouse:right'."""
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


# ── Principal ─────────────────────────────────────────────────────────────────

def check_environment() -> dict:
    """Verificação rápida: quais componentes opcionais podem ser importados + backend de áudio.

    Usada por `praxis.py --check` (integração contínua e suporte). Nunca carrega modelos."""
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
    class _Formatter(argparse.HelpFormatter):
        def add_usage(self, usage, actions, groups, prefix=None):
            return super().add_usage(usage, actions, groups, prefix="uso: ")

    parser = argparse.ArgumentParser(description="Praxis — tradutor de voz em tempo real",
                                     add_help=False, formatter_class=_Formatter)
    parser._optionals.title = "opções"
    parser.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    parser.add_argument("--src",       default="pt",
                        help="Idioma que você fala (padrão: pt)")
    parser.add_argument("--tgt",       default="en",
                        help="Idioma de saída (padrão: en)")
    parser.add_argument("--voice-out", default=None, dest="voice_out",
                        help="Voz Piper para sua fala traduzida (.onnx) — obrigatório")
    parser.add_argument("--voice-in",  default=None,  dest="voice_in",
                        help="Voz Piper para fala deles traduzida (.onnx) — ativa bilateral")
    parser.add_argument("--model",     default="auto",
                        choices=["auto", "tiny", "base", "small", "medium",
                                 "large-v2", "large-v3", "large-v3-turbo"],
                        help="auto = melhor modelo medido para este hardware "
                             "(placa de vídeo: large-v3-turbo; processador: small)")
    parser.add_argument("--mic",    default=None,
                        help="Dispositivo de entrada (veja --list-devices)")
    parser.add_argument("--output", default=None,
                        help="Dispositivo de saída para monitor (veja --list-devices)")
    parser.add_argument("--monitor", action="store_true",
                        help="Tocar tradução na saída selecionada (--output)")
    parser.add_argument("--json-out", action="store_true", dest="json_out",
                        help="Emite eventos JSON para a janela de monitoramento")
    parser.add_argument("--mode", default="vad", choices=["vad", "gate", "ptt"],
                        help="Modo de ativação: vad (automático), gate (limiar de volume RMS), ptt (botão)")
    parser.add_argument("--gate-threshold", type=float, default=0.10, dest="gate_threshold",
                        help="Limiar de volume (RMS) para o modo gate (0.0–1.0, padrão 0.10)")
    parser.add_argument("--ptt-key", default="", dest="ptt_key",
                        help="Tecla/botão de aperte para falar (PTT). Ex.: 'keyboard:ctrl_r', 'mouse:right'")
    parser.add_argument("--list-devices", action="store_true", dest="list_devices",
                        help="Lista dispositivos de áudio e sai")
    parser.add_argument("--check", action="store_true",
                        help="Verifica dependências e áudio (em JSON) e sai")
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
        print("# entradas")
        for dev_id, label in b.list_inputs():
            print(f"{dev_id}\t{label}")
        print("# saídas")
        for dev_id, label in b.list_outputs():
            print(f"{dev_id}\t{label}")
        return 0
    if not args.voice_out:
        parser.error("--voice-out é obrigatório")
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
        # Sempre remove os dispositivos virtuais, mesmo se a inicialização falhou no meio
        teardown_virtual_devices()


def _run(args: argparse.Namespace, bilateral: bool) -> int:
    _emit({"e": "progress", "pct": 20, "msg": "Carregando tradução…"})
    setup_argos(args.src, args.tgt)
    if bilateral:
        setup_argos(args.tgt, args.src)

    _emit({"e": "progress", "pct": 50, "msg": "Carregando Whisper…"})
    model = args.model
    if model == "auto":
        import praxis_accel as accel
        backend, _ = accel.choose_asr(args.device or os.environ.get("PRAXIS_DEVICE", "auto"))
        model, note = accel.recommend_model(args.src, backend)
        _emit({"e": "model", "model": model, "note": note})
        console.print(f"[dim]Modelo automático: {model}[/dim]" + (f" [yellow]({note})[/yellow]" if note else ""))
    whisper   = load_whisper(model, args.device)
    _emit({"e": "progress", "pct": 75, "msg": "Carregando voz…"})
    piper_out = load_piper(args.voice_out)
    _piper_out_ref[0] = piper_out
    piper_in  = load_piper(args.voice_in) if bilateral else None
    _emit({"e": "progress", "pct": 95, "msg": "Carregando detector de fala…"})

    _ui_state["status"] = "TRADUZINDO"

    mic_device     = resolve_mic(args.mic)
    monitor_output = args.output or None

    # PTT: começa inativo e só ativa ao pressionar o botão
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
        # O interlocutor nunca depende da tecla de falar do usuário — o PTT só vale
        # para o microfone do próprio usuário, então essa direção sempre usa o detector de fala.
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
            """Lê comandos JSON da entrada padrão para trocar configurações sem reiniciar."""
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
                        _emit({"e": "error", "msg": f"voz não encontrada: {path}"})
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
            # entrada padrão fechou (interface encerrada) → sinaliza o encerramento para remover os módulos
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
