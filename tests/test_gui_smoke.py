"""GUI smoke: build the real ConfigWindow, switch tabs, toggle theme, close.

Runs on any machine with a display (CI Linux uses xvfb). Audio is faked."""
import os
import sys
import time
import traceback

import pytest

pytestmark = pytest.mark.gui


def _has_display():
    # Never create a throwaway Tk root to probe: Tk on macOS crashes when a
    # second root is created in the same process. One window per module.
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return True


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    if not _has_display():
        pytest.skip("no display")
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


def test_window_builds_with_devices(app):
    w, errors = app
    assert w._inputs == [("mic1", "Mic 1")]
    assert w._outputs == [("spk1", "Speakers")]
    assert not errors, errors[0]


def test_tab_switch_round_trip_in_every_ui_language(app):
    w, errors = app
    import praxis_config as pc
    for lang in list(pc.UI_STRINGS)[:4]:
        w.cfg["ui_lang"] = lang
        w._on_tab_change(w._t("tab_clone"))
        _pump(w, 2)
        w._on_tab_change(w._t("tab_config"))
        _pump(w, 2)
        assert w._config_frame_outer.winfo_manager() == "pack", f"Config tab lost in ui_lang={lang}"
        assert w._clone_frame_outer.winfo_manager() == ""
    assert not errors, errors[0]


def test_theme_toggle_rebuilds_without_errors(app):
    w, errors = app
    before = w.cfg.get("theme", "light")
    w._toggle_theme()
    _pump(w)
    assert w.cfg["theme"] != before
    assert not errors, errors[0]


def test_collect_and_save_persist_ui_lang(app, monkeypatch):
    w, errors = app
    import praxis_config as pc
    monkeypatch.setattr(pc.messagebox, "showinfo", lambda *a, **k: None)
    w.cfg["ui_lang"] = "en"
    w._save()
    assert pc.load_cfg()["ui_lang"] == "en"
    assert set(w._collect()) >= {"src", "tgt", "voice_out", "mic", "mode", "ui_lang", "theme"}


def test_launch_without_voice_shows_error(app, monkeypatch):
    w, errors = app
    import praxis_config as pc
    shown = []
    monkeypatch.setattr(pc.messagebox, "showerror", lambda *a, **k: shown.append(a))
    w.voice_var.set("(nenhuma voz)")
    w._launch()
    assert shown and w._engine_proc is None


@pytest.mark.parametrize("pillow", [True, False])
def test_logo_keeps_aspect_ratio(app, monkeypatch, pillow):
    """The splash logo must never be stretched: window adapts to the logo."""
    w, errors = app
    import praxis_config as pc
    if not pillow:
        monkeypatch.setitem(sys.modules, "PIL", None)
    src = tk_png_size(pc.ASSETS_DIR / "praxis.png")
    logo = w._load_logo(380)
    assert logo is not None
    assert max(logo.width(), logo.height()) <= 380
    assert abs(logo.width() / logo.height() - src[0] / src[1]) < 0.02


def test_loading_splash_is_built_around_logo(app):
    w, errors = app
    sp, prog, lbl = w._create_loading_splash()
    try:
        sp.update_idletasks()
        logo = w._loading_photo
        assert sp.winfo_reqwidth() >= logo.width()
        img_lbl = next(c for c in sp.winfo_children() if str(c.cget("image")) == str(logo))
        assert (img_lbl.winfo_reqwidth(), img_lbl.winfo_reqheight()) >= (logo.width(), logo.height())
        # no fixed geometry: the window wraps its content on every OS / DPI scale
        sp.update()
        assert sp.winfo_width() >= max(c.winfo_reqwidth() for c in sp.winfo_children())
        assert sp.winfo_height() >= sum(c.winfo_reqheight() for c in sp.winfo_children())
    finally:
        sp.destroy()


def test_splash_wraps_content_under_display_scaling(app):
    """Windows 150% / HiDPI: scaled widgets must not be cropped and the logo
    must keep its aspect ratio."""
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
        pytest.skip("work area unknown on this display")
    assert wx <= x and x + w <= wx + ww, f"horizontal overflow {x}+{w} vs {wx}+{ww}"
    assert y + h <= wy + wh, f"vertical overflow {y}+{h} vs {wy}+{wh}"


def test_main_window_fits_usable_screen(app):
    w, errors = app
    w.deiconify()
    _assert_on_screen(w)


@pytest.mark.parametrize("scale", [1.0, 1.5])
def test_windows_fit_screen_at_any_display_scale(app, scale):
    """Main window, engine panel expansion (1120 px) and dialogs stay on screen."""
    w, errors = app
    import customtkinter as ctk
    import praxis_config as pc
    try:
        ctk.set_window_scaling(scale)
        w.deiconify()
        pc.place_window(w, 560, 900)
        _assert_on_screen(w)
        y0 = w.winfo_rooty()
        pc.place_window(w, 1120, 900, keep_position=True)     # engine started
        _assert_on_screen(w)
        for _ in range(3):                                    # start/stop must not drift
            pc.place_window(w, 560, 900, keep_position=True)
            pc.place_window(w, 1120, 900, keep_position=True)
        w.update()
        assert abs(w.winfo_rooty() - y0) <= 2, "window drifts on start/stop"
        dlg = ctk.CTkToplevel(w)
        pc.place_window(dlg, 480, 540, over=w)
        _assert_on_screen(dlg)
        dlg.destroy()
        pc.place_window(w, 3000, 3000)                        # absurd request
        _assert_on_screen(w)
    finally:
        ctk.set_window_scaling(1.0)
        pc.place_window(w, 560, 900)
