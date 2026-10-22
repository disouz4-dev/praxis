"""Teste de fumaça da interface gráfica: monta a ConfigWindow real, troca de aba,
alterna o tema e fecha.

Roda em qualquer máquina com tela (o Linux da integração contínua usa xvfb, uma
tela virtual). O áudio é simulado."""
import os
import sys
import time
import traceback

import pytest

pytestmark = pytest.mark.gui


def _has_display():
    # Estes testes abrem a janela de verdade. Para não pipocarem janelas na tela de
    # quem está trabalhando, só rodam no CI (o GitHub define CI=true) ou quando
    # pedidos com PRAXIS_TESTES_TELA=1 (ex.: num Linux com tela virtual, xvfb-run).
    if not (os.environ.get("CI") or os.environ.get("PRAXIS_TESTES_TELA") == "1"):
        return False
    # Nunca crie uma janela raiz Tk descartável só para testar: no macOS o Tk
    # trava quando uma segunda raiz é criada no mesmo processo. Uma janela por módulo.
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return True


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    if not _has_display():
        pytest.skip("teste com janela: rode com PRAXIS_TESTES_TELA=1 (o CI roda sempre)")
    monkeypatch = pytest.MonkeyPatch()
    import praxis_config as pc
    tmp = tmp_path_factory.mktemp("gui")
    monkeypatch.setattr(pc, "CONFIG_FILE", tmp / "cfg" / "config.json")
    monkeypatch.setattr(pc, "VOICES_DIR", tmp / "voices")
    import praxis_platform as plat
    from conftest import FakeBackend

    class GuiBackend(FakeBackend):
        def defaults(self):
            return "mic1", "spk1"

        def open_capture(self, device, rate, chunk):
            class Cap:
                def read(self_inner):
                    time.sleep(chunk / rate)
                    return b"\0\0" * chunk

                def close(self_inner):
                    pass
            return Cap()

        def force_rate(self, r): pass
        def restore_rate(self): pass

    monkeypatch.setattr(plat, "get_backend", lambda *a, **k: GuiBackend())
    monkeypatch.setattr(pc.ConfigWindow, "_start_meter", lambda self: None)
    errors = []
    w = pc.ConfigWindow()
    w.report_callback_exception = lambda *e: errors.append("".join(traceback.format_exception(*e)))
    for _ in range(20):
        w.update()
        time.sleep(0.02)
    yield w, errors
    try:
        w._on_close()
    except Exception:
        pass
    monkeypatch.undo()


def _pump(w, n=10):
    for _ in range(n):
        w.update()
        time.sleep(0.02)


def test_janela_monta_com_dispositivos(app):
    w, errors = app
    assert w._inputs == [("mic1", "Mic 1")]
    assert w._outputs == [("spk1", "Speakers")]
    assert not errors, errors[0]


def test_troca_de_aba_ida_e_volta_em_todo_idioma_da_interface(app):
    w, errors = app
    import praxis_config as pc
    for lang in list(pc.UI_STRINGS)[:4]:
        w.cfg["ui_lang"] = lang
        w._on_tab_change(w._t("tab_clone"))
        _pump(w, 2)
        w._on_tab_change(w._t("tab_config"))
        _pump(w, 2)
        assert w._config_frame_outer.winfo_manager() == "pack", f"Aba de configuração sumiu com ui_lang={lang}"
        assert w._clone_frame_outer.winfo_manager() == ""
    assert not errors, errors[0]


def test_alternar_tema_reconstroi_sem_erros(app):
    w, errors = app
    before = w.cfg.get("theme", "light")
    w._toggle_theme()
    _pump(w)
    assert w.cfg["theme"] != before
    assert not errors, errors[0]


def test_coletar_e_salvar_guardam_ui_lang(app, monkeypatch):
    w, errors = app
    import praxis_config as pc
    monkeypatch.setattr(pc.messagebox, "showinfo", lambda *a, **k: None)
    w.cfg["ui_lang"] = "en"
    w._save()
    assert pc.load_cfg()["ui_lang"] == "en"
    assert set(w._collect()) >= {"src", "tgt", "voice_out", "mic", "mode", "ui_lang", "theme"}


def test_iniciar_sem_voz_mostra_erro(app, monkeypatch):
    w, errors = app
    import praxis_config as pc
    shown = []
    monkeypatch.setattr(pc.messagebox, "showerror", lambda *a, **k: shown.append(a))
    w.voice_var.set("(nenhuma voz)")
    w._launch()
    assert shown and w._engine_proc is None


@pytest.mark.parametrize("pillow", [True, False])
def test_logo_mantem_proporcao(app, monkeypatch, pillow):
    """O logo da tela de abertura nunca pode ser esticado: a janela se adapta ao logo."""
    w, errors = app
    import praxis_config as pc
    if not pillow:
        monkeypatch.setitem(sys.modules, "PIL", None)
    src = tk_png_size(pc.ASSETS_DIR / "praxis.png")
    logo = w._load_logo(380)
    assert logo is not None
    assert max(logo.width(), logo.height()) <= 380
    assert abs(logo.width() / logo.height() - src[0] / src[1]) < 0.02


def test_tela_de_carregamento_e_montada_em_volta_do_logo(app):
    w, errors = app
    sp, prog, lbl = w._create_loading_splash()
    try:
        sp.update_idletasks()
        logo = w._loading_photo
        assert sp.winfo_reqwidth() >= logo.width()
        img_lbl = next(c for c in sp.winfo_children() if str(c.cget("image")) == str(logo))
        assert (img_lbl.winfo_reqwidth(), img_lbl.winfo_reqheight()) >= (logo.width(), logo.height())
        # sem tamanho fixo: a janela envolve o conteúdo em todo sistema / escala de DPI
        sp.update()
        assert sp.winfo_width() >= max(c.winfo_reqwidth() for c in sp.winfo_children())
        assert sp.winfo_height() >= sum(c.winfo_reqheight() for c in sp.winfo_children())
    finally:
        sp.destroy()


def test_tela_de_abertura_envolve_conteudo_com_escala_de_tela(app):
    """Windows em 150% / telas de alta densidade (HiDPI): elementos ampliados não
    podem ser cortados e o logo precisa manter a proporção."""
    w, errors = app
    import customtkinter as ctk
    old = ctk.ScalingTracker.window_scaling
    try:
        ctk.set_window_scaling(1.5)
        ctk.set_widget_scaling(1.5)
        sp, prog, lbl = w._create_loading_splash()
        sp.update()
        logo = w._loading_photo
        assert abs(logo.width() / logo.height() - 1.0) < 0.02
        assert sp.winfo_width() >= prog.winfo_reqwidth()
        assert sp.winfo_height() >= sum(c.winfo_reqheight() for c in sp.winfo_children())
        sp.destroy()
    finally:
        ctk.set_window_scaling(old)
        ctk.set_widget_scaling(1.0)


def tk_png_size(path):
    import struct
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def _assert_on_screen(win):
    import praxis_platform as plat
    win.update()
    x, y = win.winfo_rootx(), win.winfo_rooty()
    w, h = win.winfo_width(), win.winfo_height()
    wx, wy, ww, wh = plat.work_area(win, point=(x + w // 2, y + h // 2))
    if not ww:
        pytest.skip("área de trabalho desconhecida nesta tela")
    assert wx <= x and x + w <= wx + ww, f"estouro horizontal {x}+{w} vs {wx}+{ww}"
    assert y + h <= wy + wh, f"estouro vertical {y}+{h} vs {wy}+{wh}"


def test_janela_principal_cabe_na_area_util_da_tela(app):
    w, errors = app
    w.deiconify()
    _assert_on_screen(w)


def test_janela_principal_fica_no_meio_sem_esticar(app):
    """Janela média e centralizada — não esticada até a altura da tela."""
    w, errors = app
    import praxis_config as pc
    import praxis_platform as plat
    pc.place_window(w, pc.ConfigWindow.WIN_W, pc.ConfigWindow.WIN_H)
    w.deiconify()
    w.update()
    wx, wy, ww, wh = plat.work_area(w)
    if not ww:
        pytest.skip("área de trabalho desconhecida")
    assert w.winfo_height() <= pc.ConfigWindow.WIN_H + 2
    assert w.winfo_width() <= pc.ConfigWindow.WIN_W + 2
    if wh > pc.ConfigWindow.WIN_H + 100:          # sobra espaço → visivelmente centralizada
        cy = w.winfo_rooty() + w.winfo_height() // 2
        assert abs(cy - (wy + wh // 2)) < 60, "janela não centralizada na vertical"


@pytest.mark.parametrize("scale", [1.0, 1.5])
def test_janelas_cabem_na_tela_em_qualquer_escala(app, scale):
    """A janela principal, a expansão do painel do motor (1120 px) e as caixas de diálogo ficam dentro da tela."""
    w, errors = app
    import customtkinter as ctk
    import praxis_config as pc
    try:
        ctk.set_window_scaling(scale)
        w.deiconify()
        pc.place_window(w, 560, 720)
        _assert_on_screen(w)
        y0 = w.winfo_rooty()
        pc.place_window(w, 1120, 720, keep_position=True)     # motor iniciado
        _assert_on_screen(w)
        for _ in range(3):                                    # iniciar/parar não pode fazer a janela se deslocar
            pc.place_window(w, 560, 720, keep_position=True)
            pc.place_window(w, 1120, 720, keep_position=True)
        w.update()
        assert abs(w.winfo_rooty() - y0) <= 2, "a janela se desloca ao iniciar/parar"
        dlg = ctk.CTkToplevel(w)
        pc.place_window(dlg, 480, 540, over=w)
        _assert_on_screen(dlg)
        dlg.destroy()
        pc.place_window(w, 3000, 3000)                        # pedido absurdo
        _assert_on_screen(w)
    finally:
        ctk.set_window_scaling(1.0)
        pc.place_window(w, 560, 720)
