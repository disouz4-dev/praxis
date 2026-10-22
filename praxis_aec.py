"""Cancelamento de eco acústico: tira do microfone o som que o próprio Praxis tocou
no alto-falante, deixando só a voz do usuário.

Como funciona, sem siglas: o Praxis sabe exatamente qual áudio mandou para o
alto-falante (a "referência"). O som chega ao microfone atrasado, mais baixo e
"borrado" pela sala. Um filtro adaptativo aprende, bloco a bloco, esse caminho
alto-falante → sala → microfone, prevê o eco e o subtrai. Diferente da trava de
eco (que ensurdece o microfone enquanto o alto-falante toca), aqui o usuário pode
falar por cima da tradução.

Tudo em numpy, sem dependências novas: filtro adaptativo no domínio da
frequência, em blocos (o mesmo princípio do cancelador do Speex/WebRTC).
"""
from __future__ import annotations

import threading

import numpy as np


class EchoReference:
    """Guarda o áudio tocado no alto-falante com a hora (relógio monotônico) em que
    começou, para entregar ao cancelador o trecho que coincide com cada bloco do microfone."""

    def __init__(self, sr: int = 16000, keep_s: float = 20.0) -> None:
        self.sr = sr
        self.keep = int(keep_s * sr)
        self._lock = threading.Lock()
        self._pieces: list[tuple[int, np.ndarray]] = []    # (amostra inicial, áudio)
        self.used = False                                   # algo já tocou no alto-falante

    def _idx(self, t: float) -> int:
        return int(round(t * self.sr))

    def add(self, audio: np.ndarray, t_start: float) -> None:
        i = self._idx(t_start)
        with self._lock:
            self.used = True
            self._pieces.append((i, np.asarray(audio, np.float32)))
            cut = i - self.keep
            self._pieces = [p for p in self._pieces if p[0] + len(p[1]) > cut]

    def get(self, t_start: float, n: int) -> np.ndarray:
        out = np.zeros(n, np.float32)
        a = self._idx(t_start)
        with self._lock:
            for i, x in self._pieces:
                lo, hi = max(a, i), min(a + n, i + len(x))
                if lo < hi:
                    out[lo - a:hi - a] += x[lo - i:hi - i]
        return out

    def active(self, t_start: float, t_end: float) -> bool:
        a, b = self._idx(t_start), self._idx(t_end)
        with self._lock:
            return any(i < b and i + len(x) > a for i, x in self._pieces)


class EchoCanceller:
    """Filtro adaptativo em blocos (no domínio da frequência, "overlap-save"), com
    dois filtros, como nos canceladores profissionais:

      aprendiz  aprende rápido o tempo todo — inclusive quando o usuário fala por
                cima da tradução, o que às vezes o faz errar
      oficial   o que de fato limpa o microfone; só copia o aprendiz quando ele
                está comprovadamente tirando mais eco (e o aprendiz volta ao
                oficial se desandar)

    Assim o cancelador aprende mesmo com o usuário falando sem parar, sem que a
    voz dele estrague o que já foi aprendido.

    block       amostras por bloco (o mesmo bloco do detector de fala: 512 = 32 ms)
    tail_s      quanto tempo de eco o filtro cobre (atraso do aparelho + reverberação da sala)
    """

    def __init__(self, block: int = 512, tail_s: float = 0.6, mu: float = 0.6,
                 suppress: bool = True) -> None:
        self.N = block
        self.P = max(1, int(np.ceil(tail_s * 16000 / block)))
        self.mu = mu
        self.suppress = suppress
        K = block + 1
        self.Wb = np.zeros((self.P, K), np.complex128)       # aprendiz
        self.Wf = np.zeros((self.P, K), np.complex128)       # oficial
        self.X = np.zeros((self.P, K), np.complex128)        # espectros da referência recente
        self.prev_ref = np.zeros(block, np.float64)
        self.Pe = np.full(K, 1e-6)                           # potência do resíduo do aprendiz por faixa
        self.gain = self.spread = 0.0                        # comparação aprendiz × oficial
        self.residual_gate = True     # silencia blocos que são só resto de eco
        self.gate_ratio = 1.0         # resíduo abaixo desta fração do eco previsto → silêncio
        self.dt_k = 1.0              # quanto um resíduo grande (voz do usuário) freia o aprendiz
        self.copies = 0
        # supressor do eco que sobra (janela de 50%, raiz de Hann: reconstrução perfeita)
        self._win = np.sqrt(np.hanning(2 * block + 1)[:-1])
        self._prev_e = np.zeros(block, np.float64)
        self._prev_y = np.zeros(block, np.float64)
        self._ola = np.zeros(block, np.float64)
        self._g = np.ones(K)

    def reset(self) -> None:
        self.__init__(self.N, self.P * self.N / 16000, self.mu, self.suppress)

    def _predict(self, W: np.ndarray) -> np.ndarray:
        return np.fft.irfft(np.sum(W * self.X, axis=0))[self.N:]

    def process(self, mic: np.ndarray, ref: np.ndarray) -> np.ndarray:
        N = self.N
        mic = np.asarray(mic, np.float64)
        ref = np.asarray(ref, np.float64)
        ref_on = float(np.max(np.abs(ref))) > 1e-5 or float(np.max(np.abs(self.prev_ref))) > 1e-5
        x2 = np.concatenate([self.prev_ref, ref])
        self.prev_ref = ref
        self.X = np.roll(self.X, 1, axis=0)
        self.X[0] = np.fft.rfft(x2)
        if not ref_on and not np.any(self.X):
            return self._out_from(mic, np.zeros(N))
        yf = self._predict(self.Wf)
        ef = mic - yf
        if ref_on:
            yb = self._predict(self.Wb)
            eb = mic - yb
            Eb = np.fft.rfft(np.concatenate([np.zeros(N), eb]))
            S = np.sum(np.abs(self.X) ** 2, axis=0)          # energia da referência em toda a memória do filtro
            # passo menor quando o resíduo é grande (voz do usuário por cima)
            self.Pe = 0.7 * self.Pe + 0.3 * np.abs(Eb) ** 2
            step = self.mu * S / (S + self.dt_k * self.Pe + 1e-12)
            G = np.conj(self.X) * (step * Eb / (S + 1e-3 * float(np.mean(S)) + 1e-8))
            g = np.fft.irfft(G, axis=1)
            g[:, N:] = 0.0                                    # restrição do overlap-save
            self.Wb += np.fft.rfft(g, axis=1)
            # compara os dois filtros. A voz do usuário entra igual nos dois resíduos e se
            # cancela na diferença: (ef − eb) ≈ eco que só o aprendiz tirou. Medido na
            # escala de quanto as previsões diferem, para não depender do volume da voz.
            a = 0.85
            self.gain = a * self.gain + (1 - a) * float(np.mean(ef ** 2) - np.mean(eb ** 2))
            self.spread = a * self.spread + (1 - a) * float(np.mean((yb - yf) ** 2))
            if self.gain > 0.3 * self.spread and self.spread > 1e-10:
                self.Wf = self.Wb.copy()                      # aprendiz tira mais eco: vira o oficial
                self.copies += 1
                self.gain = self.spread = 0.0
                yf, ef = yb, eb
            elif self.gain < -4.0 * self.spread and self.spread > 1e-10:
                self.Wb = self.Wf.copy()                      # aprendiz desandou: recomeça do oficial
                self.gain = self.spread = 0.0
        out = self._out_from(ef, yf)
        if self.residual_gate and ref_on:
            # o que sobrou é bem mais fraco que o eco previsto: é resto de eco, não a
            # voz do usuário (que, falando por cima, chega bem mais forte que o eco)
            ye = float(np.mean(yf ** 2))
            if ye > 1e-9 and float(np.mean(ef ** 2)) < self.gate_ratio * ye:
                out = out * 0.0
        return out

    def _out_from(self, e: np.ndarray, y: np.ndarray) -> np.ndarray:
        if not self.suppress:
            return e.astype(np.float32)
        # supressão espectral do eco que o filtro não tirou: faixas onde o eco previsto
        # domina o resíduo são atenuadas (mais forte logo após o alto-falante tocar)
        N = self.N
        fe = np.fft.rfft(self._win * np.concatenate([self._prev_e, e]))
        fy = np.fft.rfft(self._win * np.concatenate([self._prev_y, y]))
        self._prev_e, self._prev_y = e, y
        pe, py = np.abs(fe) ** 2, np.abs(fy) ** 2
        leak = 0.5                                           # fração do eco previsto que sobra
        g = np.clip(1.0 - leak * py / (pe + 1e-10), 0.08, 1.0)
        self._g = np.maximum(g, 0.6 * self._g + 0.4 * g) if py.sum() > 0 else np.ones_like(g)
        out = np.fft.irfft(fe * self._g) * self._win
        res = self._ola + out[:N]
        self._ola = out[N:]
        return res.astype(np.float32)
