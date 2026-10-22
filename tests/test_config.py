"""Módulo da interface (praxis_config.py): catálogo, vozes, gravação da configuração, traduções da interface (i18n), downloads."""
import io
import json

import pytest


def test_url_do_catalogo_usa_codificacao_percentual(cfg_module):
    pc = cfg_module
    tug = next(v for v in pc.VOICE_CATALOG if v["speaker"] == "tugão")
    url = pc._catalog_url(tug, ".json")
    url.encode("ascii")                                   # tem que ser só ASCII
    assert "tug%C3%A3o" in url and url.endswith(".onnx.json")


def test_entradas_do_catalogo_bem_formadas(cfg_module):
    pc = cfg_module
    names = set()
    for v in pc.VOICE_CATALOG:
        assert v["quality"] in ("x_low", "low", "medium", "high")
        assert v["locale"].split("_")[0] == v["lang"]
        fn = pc._catalog_filename(v)
        assert fn not in names
        names.add(fn)


def test_codigo_de_idioma_da_voz_e_filtro(cfg_module):
    pc = cfg_module
    assert pc._voice_lang_code("/v/it_IT-paola-medium.onnx") == "it"
    voices = [("/v/pt_BR-faber-medium.onnx", "Faber"), ("/v/en_US-ryan-medium.onnx", "Ryan"),
              ("/v/clones/me.wav", "🎙 Me")]
    assert [l for _, l in pc._voices_for_lang(voices, "pt")] == ["Faber", "🎙 Me"]


def test_melhor_voz_do_catalogo_prefere_padrao_depois_media(cfg_module):
    pc = cfg_module
    assert pc._best_catalog_voice("de")["speaker"] == "thorsten"     # medida como mais rápida, "padrão"
    assert pc._best_catalog_voice("it")["quality"] == "medium"
    assert pc._best_catalog_voice("xx") is None


def test_carrega_config_padrao_quando_ausente(cfg_module):
    pc = cfg_module
    assert pc.load_cfg() == {**pc.DEFAULT_CFG, **{k: v for k, v in pc.load_cfg().items()}}


def test_carrega_config_resiste_a_arquivo_corrompido_e_tipos_errados(cfg_module):
    pc = cfg_module
    pc.CONFIG_FILE.parent.mkdir(parents=True)
    pc.CONFIG_FILE.write_text("{not json")
    assert pc.load_cfg()["mode"] == pc.DEFAULT_CFG["mode"]
    pc.CONFIG_FILE.write_text(json.dumps({"gate_threshold": "loud", "voice_out": None, "mode": "ptt"}))
    cfg = pc.load_cfg()
    assert isinstance(cfg["gate_threshold"], float)
    assert cfg["voice_out"] == pc.DEFAULT_CFG["voice_out"]
    assert cfg["mode"] == "ptt"
    pc.CONFIG_FILE.write_text("[1, 2]")
    assert pc.load_cfg()["mode"] == pc.DEFAULT_CFG["mode"]


def test_salvar_e_reler_config_e_atomico(cfg_module):
    pc = cfg_module
    cfg = dict(pc.DEFAULT_CFG, src="es", ui_lang="de")
    pc.save_cfg(cfg)
    assert json.loads(pc.CONFIG_FILE.read_text(encoding="utf-8"))["ui_lang"] == "de"
    assert not list(pc.CONFIG_FILE.parent.glob("*.tmp"))
    assert pc.load_cfg()["src"] == "es"


def test_i18n_todos_os_idiomas_tem_as_mesmas_chaves(cfg_module):
    pc = cfg_module
    base = set(pc.UI_STRINGS["pt"])
    for lang, table in pc.UI_STRINGS.items():
        assert set(table) == base, f"{lang}: faltando {base - set(table)}"


def test_lista_vozes_onnx_e_clones(cfg_module):
    pc = cfg_module
    pc.VOICES_DIR.mkdir()
    (pc.VOICES_DIR / "pt_BR-faber-medium.onnx").write_bytes(b"x")
    clones = pc.VOICES_DIR / "clones"
    clones.mkdir()
    (clones / "me.wav").write_bytes(b"x")
    (clones / "me.json").write_text(json.dumps({"name": "Diego", "wav": "me.wav", "type": "omnivoice"}))
    (clones / "broken.json").write_text("{")
    labels = [l for _, l in pc.get_voices()]
    assert "pt_BR-faber-medium" in labels and "🎙 Diego" in labels


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def test_download_dos_arquivos_de_voz_atomico(cfg_module, monkeypatch):
    pc = cfg_module
    v = pc.VOICE_CATALOG[0]
    monkeypatch.setattr(pc.urllib.request, "urlopen", lambda url, timeout=0: _Resp(b"data"))
    pc._download_voice_files(v)
    fn = pc._catalog_filename(v)
    assert (pc.VOICES_DIR / fn).read_bytes() == b"data"
    assert (pc.VOICES_DIR / f"{fn}.json").exists()
    assert not list(pc.VOICES_DIR.glob("*.part"))


def test_falha_no_download_de_voz_nao_deixa_nada(cfg_module, monkeypatch):
    pc = cfg_module
    v = pc.VOICE_CATALOG[1]
    calls = []

    def fake(url, timeout=0):
        calls.append(url)
        if url.endswith(".onnx"):
            raise OSError("connection reset")
        return _Resp(b"{}")
    monkeypatch.setattr(pc.urllib.request, "urlopen", fake)
    with pytest.raises(OSError):
        pc._download_voice_files(v)
    assert list(pc.VOICES_DIR.iterdir()) == []          # nenhuma voz pela metade "instalada"


def test_listas_de_audio_nunca_dao_erro(cfg_module, monkeypatch):
    pc = cfg_module
    import praxis_platform as plat

    class Boom:
        def list_inputs(self): raise RuntimeError
        def list_outputs(self): raise RuntimeError
        def defaults(self): raise RuntimeError
    monkeypatch.setattr(plat, "get_backend", lambda: Boom())
    assert pc.get_audio_inputs() == [] and pc.get_audio_outputs() == []
    assert pc._pa_defaults() == ("", "")


def test_sem_chamadas_fixas_exclusivas_do_linux():
    """Proteção contra regressão no suporte a vários sistemas operacionais."""
    from conftest import ROOT
    src = (ROOT / "praxis_config.py").read_text(encoding="utf-8") + \
        (ROOT / "praxis.py").read_text(encoding="utf-8")
    for bad in ('"aplay"', '"xrandr"', '"/tmp/', "'/tmp/", '".local/share/praxis/venv',
                '["parec"', '["pacat"', '"pw-metadata"'):
        assert bad not in src, f"Chamada exclusiva do Linux esquecida na interface/motor: {bad}"



def test_primeira_execucao_herda_o_idioma_do_sistema(cfg_module, monkeypatch):
    import praxis_platform as plat
    pc = cfg_module
    monkeypatch.setattr(plat, "system_language", lambda: "de")
    cfg = pc.load_cfg()                                   # ainda não existe configuração salva
    assert (cfg["ui_lang"], cfg["src"], cfg["tgt"]) == ("de", "de", "en")


def test_escolha_salva_vale_mais_que_o_idioma_do_sistema(cfg_module, monkeypatch):
    import praxis_platform as plat
    pc = cfg_module
    monkeypatch.setattr(plat, "system_language", lambda: "de")
    pc.save_cfg(dict(pc.DEFAULT_CFG, ui_lang="pt", src="pt", tgt="es"))
    cfg = pc.load_cfg()
    assert (cfg["ui_lang"], cfg["src"], cfg["tgt"]) == ("pt", "pt", "es")
