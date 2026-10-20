"""Testes da varredura de defeitos da interface (praxis_config.py).

Só lógica pura: nenhuma janela Tk é criada (no macOS uma segunda janela raiz no
mesmo processo trava o Tk, e test_gui_smoke.py já cria a dele). Os métodos da
ConfigWindow rodam sobre um objeto falso que imita só o que cada método usa."""
from __future__ import annotations

import inspect
import json
import sys
import threading
import time
import types

import numpy as np
import pytest

import praxis_config as pc


# ── Objeto falso que empresta os métodos da ConfigWindow ─────────────────────

class FalsoWidget:
    """Guarda a última configuração recebida, como um botão/rótulo do Tk."""

    def __init__(self) -> None:
        self.cfg: dict = {}
        self.valor = 0.0

    def configure(self, **kw) -> None:
        self.cfg.update(kw)

    def set(self, v) -> None:
        self.valor = v

    def get(self):
        return self.valor


class FalsaVar:
    def __init__(self, v=None) -> None:
        self.v = v

    def get(self):
        return self.v

    def set(self, v) -> None:
        self.v = v


class FalsaJanela:
    """Substituto da ConfigWindow: atributos que faltam vêm da classe real,
    já ligados a este objeto. O `after` só agenda; os testes rodam a fila na mão."""

    def __init__(self, **attrs) -> None:
        self._fila: dict[int, tuple] = {}
        self._prox_id = 0
        self.__dict__.update(attrs)

    def __getattr__(self, nome):
        bruto = inspect.getattr_static(pc.ConfigWindow, nome)
        if isinstance(bruto, staticmethod):
            return bruto.__func__
        if isinstance(bruto, property):
            return bruto.fget(self)
        if inspect.isfunction(bruto):
            return types.MethodType(bruto, self)
        return bruto

    def _t(self, chave: str) -> str:
        return pc.UI_STRINGS["pt"].get(chave, chave)

    def after(self, ms, fn=None, *args):
        self._prox_id += 1
        self._fila[self._prox_id] = (ms, fn, args)
        return self._prox_id

    def after_cancel(self, after_id) -> None:
        self._fila.pop(after_id, None)

    def rodar_fila(self, ms: int | None = None) -> int:
        """Roda as tarefas agendadas (todas, ou só as com esse atraso). Devolve quantas rodou."""
        rodadas = 0
        for aid, (atraso, fn, args) in list(self._fila.items()):
            if ms is not None and atraso != ms:
                continue
            self._fila.pop(aid, None)
            fn(*args)
            rodadas += 1
        return rodadas


# ── (a) tecla de aperte-para-falar ───────────────────────────────────────────

def test_tecla_especial_usa_o_nome():
    tecla = types.SimpleNamespace(name="ctrl_r")
    assert pc._ptt_key_to_str(tecla) == "keyboard:ctrl_r"


def test_tecla_de_letra_usa_o_caractere():
    # KeyCode do pynput não tem .name, só .char — antes a letra nunca era salva
    tecla = types.SimpleNamespace(char="A", vk=0)
    assert pc._ptt_key_to_str(tecla) == "keyboard:a"


@pytest.mark.parametrize("char", [None, "\x01", " "])
def test_tecla_que_nao_da_para_salvar_devolve_none(char):
    assert pc._ptt_key_to_str(types.SimpleNamespace(char=char)) is None


def test_tecla_de_letra_com_pynput_de_verdade():
    kb = pytest.importorskip("pynput.keyboard")
    salvo = pc._ptt_key_to_str(kb.KeyCode.from_char("a"))
    assert salvo == "keyboard:a"
    # O motor (praxis.py) lê o mesmo texto com KeyCode.from_char
    nome = salvo.split(":", 1)[1]
    assert kb.KeyCode.from_char(nome) == kb.KeyCode.from_char("a")
    assert pc._ptt_key_to_str(kb.Key.ctrl_r) == "keyboard:ctrl_r"


# ── (b) cronômetro da gravação de referência ─────────────────────────────────

def _janela_gravacao() -> FalsaJanela:
    return FalsaJanela(
        _meter_stream=object(),
        _ov_rec_btn=FalsoWidget(), _ov_rec_status=FalsoWidget(),
        _ov_rec_prog=FalsoWidget(), _ov_rec_frames=[],
        MUTED="#000",
    )


def test_parar_e_regravar_rapido_nao_duplica_o_cronometro():
    j = _janela_gravacao()
    j._ov_start_recording()
    j._ov_stop_recording()          # sem áudio: só para
    j._ov_start_recording()         # regrava antes do tique de 1 s
    ticks = [a for a in j._fila.values() if a[0] == 1000]
    assert len(ticks) == 1, "deveria haver um único tique pendente do cronômetro"
    inicio = j._ov_rec_timer
    for _ in range(7):
        j.rodar_fila(1000)
    assert j._ov_rec_timer == inicio + 7, "o cronômetro correu em dobro"
    assert j._ov_rec_active, "a gravação parou sozinha antes do limite"


def test_parar_cancela_o_tique_pendente():
    j = _janela_gravacao()
    j._ov_start_recording()
    j._ov_stop_recording()
    assert not [a for a in j._fila.values() if a[0] == 1000]


def test_cronometro_para_sozinho_no_limite():
    j = _janela_gravacao()
    j._ov_start_recording()
    for _ in range(pc.ConfigWindow._OV_REF_MAX_S + 3):
        j.rodar_fila(1000)
    assert j._ov_rec_timer == pc.ConfigWindow._OV_REF_MAX_S
    assert not j._ov_rec_active


# ── (c) OmniVoice: uma tarefa por vez ────────────────────────────────────────

def _janela_omnivoice(**extra) -> FalsaJanela:
    attrs = dict(
        _ov_lock=threading.Lock(), _ov_gen_running=False, _testing=False,
        _clone_test_btns=[], _ov_gen_btn=FalsoWidget(), _ov_play_btn=FalsoWidget(),
        _ov_status_lbl=FalsoWidget(), MUTED="#000",
    )
    attrs.update(extra)
    return FalsaJanela(**attrs)


def test_gerar_recusa_enquanto_um_teste_roda(monkeypatch):
    j = _janela_omnivoice(
        _testing=True,
        _ov_ref_path=FalsaVar("ref.wav"), _ov_ref_text=FalsaVar(""),
        _ov_gen_text=types.SimpleNamespace(get=lambda *a: "olá"),
    )
    iniciadas = []
    monkeypatch.setattr(pc.threading, "Thread", lambda *a, **k: iniciadas.append(k))
    j._ov_generate()
    assert not iniciadas, "não pode iniciar a geração com um teste em andamento"
    assert "Aguarde" in j._ov_status_lbl.cfg["text"]


def test_testar_recusa_enquanto_gera(monkeypatch):
    j = _janela_omnivoice(_ov_gen_running=True)
    iniciadas = []
    monkeypatch.setattr(pc.threading, "Thread", lambda *a, **k: iniciadas.append(k))
    j._test_clone("clone.wav", "")
    assert not iniciadas
    assert j._testing is False


def test_botoes_desligam_e_religam():
    b1, b2 = FalsoWidget(), FalsoWidget()
    j = _janela_omnivoice(_clone_test_btns=[b1, b2])
    j._ov_set_busy(True)
    assert j._ov_gen_btn.cfg["state"] == "disabled"
    assert b1.cfg["state"] == b2.cfg["state"] == "disabled"
    j._ov_set_busy(False)
    assert j._ov_gen_btn.cfg["state"] == "normal"
    assert b1.cfg["state"] == "normal"
    assert b1.cfg["text"] == j._t("btn_test")


def test_duas_geracoes_juntas_carregam_o_modelo_uma_vez_so(monkeypatch, tmp_path):
    cargas, em_uso, maximo = [], [0], [0]
    trava_contagem = threading.Lock()

    class Modelo:
        def create_voice_clone_prompt(self, **kw):
            return object()

        def generate(self, **kw):
            with trava_contagem:
                em_uso[0] += 1
                maximo[0] = max(maximo[0], em_uso[0])
            time.sleep(0.05)
            with trava_contagem:
                em_uso[0] -= 1
            return [np.zeros(16, dtype=np.float32)]

    def carregar(*a, **k):
        cargas.append(1)
        time.sleep(0.1)
        return Modelo()

    falso_omni = types.SimpleNamespace(OmniVoice=types.SimpleNamespace(from_pretrained=carregar))
    falso_torch = types.SimpleNamespace(
        cuda=types.SimpleNamespace(is_available=lambda: False, empty_cache=lambda: None),
        float16="f16", float32="f32")
    falso_sf = types.SimpleNamespace(write=lambda *a, **k: None)
    monkeypatch.setitem(sys.modules, "omnivoice", falso_omni)
    monkeypatch.setitem(sys.modules, "torch", falso_torch)
    monkeypatch.setitem(sys.modules, "soundfile", falso_sf)
    monkeypatch.setattr(pc.plat, "temp_path", lambda nome: str(tmp_path / nome))

    j = _janela_omnivoice(_ov_model=None)
    j._patch_ov_transcribe = lambda m: m
    j._ov_warmup = lambda m, t: None
    j._trim_ref_wav = lambda p, max_s=5.0: p

    ts = [threading.Thread(target=j._ov_generate_worker, args=("r.wav", "", "olá", "pt"))
          for _ in range(2)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(5)
    assert len(cargas) == 1, "o modelo foi carregado duas vezes (estoura a memória da placa)"
    assert maximo[0] == 1, "duas gerações rodaram ao mesmo tempo"
    assert not j._ov_lock.locked()


# ── (d) apagar clone ─────────────────────────────────────────────────────────

def _clone_em_disco(pasta, nome="Diego"):
    pasta.mkdir(parents=True, exist_ok=True)
    wav = pasta / f"{nome}.wav"
    wav.write_bytes(b"RIFF")
    jp = pasta / f"{nome}.json"
    jp.write_text(json.dumps({"name": nome, "wav": wav.name}))
    return jp, wav


def _janela_vozes(tmp_path, monkeypatch, clone_wav):
    monkeypatch.setattr(pc, "VOICES_DIR", tmp_path / "voices")
    label = "🎙 Diego"
    j = FalsaJanela(
        _voices=[("/v/pt_BR-faber-medium.onnx", "♂ faber"), (str(clone_wav), label)],
        _voice_menu=FalsoWidget(), voice_var=FalsaVar(label),
        _show_clones=FalsaVar(True), _clone_voice_path=str(clone_wav),
        _clone_voice_name="Diego", _clone_list_frame=None,
    )
    j._tgt_code = lambda: "pt"
    j._show_dl_card = lambda code: None
    j._refresh_clone_list = lambda: None
    return j


def test_apagar_clone_pede_confirmacao_e_respeita_o_nao(tmp_path, monkeypatch):
    jp, wav = _clone_em_disco(tmp_path / "voices" / "clones")
    j = _janela_vozes(tmp_path, monkeypatch, wav)
    perguntas = []
    monkeypatch.setattr(pc.messagebox, "askyesno",
                        lambda titulo, msg, **k: perguntas.append(msg) or False)
    j._delete_clone(jp)
    assert perguntas and "Diego" in perguntas[0]
    assert jp.exists() and wav.exists(), "apagou mesmo com a resposta 'não'"


def test_apagar_clone_escolhido_troca_a_voz_de_saida(tmp_path, monkeypatch):
    jp, wav = _clone_em_disco(tmp_path / "voices" / "clones")
    j = _janela_vozes(tmp_path, monkeypatch, wav)
    monkeypatch.setattr(pc.messagebox, "askyesno", lambda *a, **k: True)
    j._delete_clone(jp)
    assert not jp.exists() and not wav.exists()
    assert all(p != str(wav) for p, _ in j._voices)
    assert j.voice_var.get() != "🎙 Diego", "o clone apagado continuou escolhido"
    assert "🎙 Diego" not in j._voice_menu.cfg["values"]
    assert j._clone_voice_path is None


def test_pasta_de_clones_acompanha_voices_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(pc, "VOICES_DIR", tmp_path)
    assert FalsaJanela().CLONES_DIR == tmp_path / "clones"
