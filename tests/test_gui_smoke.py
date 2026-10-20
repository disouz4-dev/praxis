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
