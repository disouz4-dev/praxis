// Praxis — janela. Toda a lógica está no motor; aqui só a interface.
const { invoke } = window.__TAURI__.core;
const { listen } = window.__TAURI__.event;

const $ = (id) => document.getElementById(id);
let I18N = null;      // textos da interface em 14 idiomas (os mesmos do Praxis em Python)
let ESTADO = null;    // vindo do motor: dispositivos, idiomas liberados, placa de vídeo
let cfg = {};
let rodando = false;

const t = (k) => (I18N.strings[cfg.ui_lang] || I18N.strings.pt)[k] || I18N.strings.pt[k] || k;
// texto com partes variáveis: tf("dl_progress", {what, got, total}) troca {what}, {got}, {total}
const tf = (k, v = {}) => t(k).replace(/\{(\w+)\}/g, (m, n) => (n in v ? v[n] : m));
const nomeIdioma = (c) => ((I18N.lang_names[cfg.ui_lang] || {})[c]) || I18N.native_names[c] || c;

// Textos montados pelo código: guarda como gerar cada um, para refazer quando o idioma muda.
const VIVOS = {};
function vivo(id, gerar) { VIVOS[id] = gerar; $(id).textContent = gerar(); }
function fixo(id, texto) { delete VIVOS[id]; $(id).textContent = texto; }   // texto que vem pronto (do motor)

function aplicarTextos() {
  document.querySelectorAll("[data-t]").forEach((el) => (el.textContent = t(el.dataset.t)));
  document.querySelectorAll("[data-t-title]").forEach((el) => (el.title = t(el.dataset.tTitle)));
  for (const [id, gerar] of Object.entries(VIVOS)) $(id).textContent = gerar();
  $("iniciar").textContent = rodando ? t("btn_stop") : t("btn_start");
  document.documentElement.lang = cfg.ui_lang;
  document.documentElement.dir = cfg.ui_lang === "ar" ? "rtl" : "ltr";
}

function opcao(valor, texto, desativada = false) {
  const o = document.createElement("option");
  o.value = valor; o.textContent = texto; o.disabled = desativada;
  return o;
}

function preencherIdiomas() {
  const src = $("src"), tgt = $("tgt");
  src.replaceChildren(); tgt.replaceChildren();
  for (const i of ESTADO.idiomas) {
    const marca = i.liberado ? "" : " " + t("lang_unavailable");
    src.append(opcao(i.codigo, nomeIdioma(i.codigo) + marca, !i.liberado));
    if (i.tem_voz) tgt.append(opcao(i.codigo, nomeIdioma(i.codigo)));
  }
  src.value = cfg.src; tgt.value = cfg.tgt;
  if (src.value !== cfg.src || src.selectedOptions[0]?.disabled) {
    const livre = ESTADO.idiomas.find((i) => i.liberado);
    if (livre) src.value = livre.codigo;
  }
  if (!tgt.value) tgt.value = cfg.src === "en" ? "pt" : "en";
  verificarIdiomas();
}

// "parakeet-ultra-int8" → "Parakeet ultra"; "large-v3-turbo" → "Whisper large-v3-turbo"
function nomeModelo(m) {
  if (!m) return "?";
  if (m.startsWith("parakeet")) {
    const v = m.includes("ultra") ? "ultra" : m.includes("-ja-") ? t("model_ja") : m.includes("v2") ? t("model_v2_en") : "v3";
    return "Parakeet " + v;
  }
  return "Whisper " + m;
}

function diagnostico() {
  const info = (c) => ESTADO.idiomas.find((i) => i.codigo === c);
  const linha = (c) => {
    const i = info(c);
    if (!i) return "";
    const pct = () => (i.erro * 100).toLocaleString(cfg.ui_lang, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    const erro = i.erro == null ? t("diag_none") : tf("diag_err", { pct: pct() });
    return tf("diag_line", { model: nomeModelo(i.modelo), lang: nomeIdioma(c), err: erro });
  };
  const s = $("src").value, d = $("tgt").value, bi = $("bilateral").checked;
  vivo("diagnostico", () => [linha(s), bi ? linha(d) : ""].filter(Boolean).join(" · "));
}

function verificarIdiomas() {
  diagnostico();
  const s = $("src").value, d = $("tgt").value;
  const info = (c) => ESTADO.idiomas.find((i) => i.codigo === c) || { liberado: true };
  const bi = $("bilateral").checked;
  // o "motivo" vem do motor como está; só a moldura do aviso é traduzida
  const aviso = () => s === d ? t("warn_same_lang")
    : !info(s).liberado ? info(s).motivo
    : bi && !info(d).liberado ? tf("warn_bilateral", { lang: nomeIdioma(d), reason: info(d).motivo })
    : "";
  vivo("aviso_idioma", aviso);
  $("aviso_idioma").hidden = !aviso();
  $("iniciar").disabled = !rodando && !!aviso();
}

function preencherDispositivos() {
  const padrao = t("lbl_sys_default");
  for (const [id, lista] of [["mic", ESTADO.entradas], ["output", ESTADO.saidas]]) {
    const sel = $(id);
    sel.replaceChildren(opcao("", padrao));
    // os cabos virtuais do Praxis não são microfone nem fone de ninguém: escolhê-los fazia a
    // tradução voltar para dentro do Praxis
    for (const n of lista) if (!/^(Monitor of )?Praxis[ _]|VB-Audio Virtual Cable|BlackHole/.test(n)) sel.append(opcao(n, n));
    sel.value = cfg[id] || "";
    if (sel.selectedIndex < 0) sel.value = "";   // o aparelho salvo sumiu (desplugado): volta ao padrão
  }
}

function coletar() {
  return {
    ...cfg,
    src: $("src").value, tgt: $("tgt").value,
    mic: $("mic").value || null, output: $("output").value || null,
    monitor: $("monitor").checked, headphones: $("headphones").checked,
    bilateral: $("bilateral").checked,
    model: $("model").value, translator: $("translator").value,
  };
}

async function salvar() {
  cfg = coletar();
  try { await invoke("salvar_config", { config: cfg }); } catch (e) { console.warn(e); }
}

// status com texto do motor (vem pronto)
function status(texto, tipo = "") {
  fixo("status_texto", texto);
  $("status_ponto").className = tipo;
}

// status com texto da interface (chave do i18n.json)
function statusT(chave, tipo = "") {
  vivo("status_texto", () => t(chave));
  $("status_ponto").className = tipo;
}

function adicionarFala(dir, original, traducao) {
  const c = $("conversa");
  const div = document.createElement("div");
  div.className = "fala " + dir;
  div.innerHTML = '<div class="original"></div><div class="traducao"></div>';
  div.querySelector(".original").textContent = original;
  div.querySelector(".traducao").textContent = traducao;
  c.append(div);
  c.scrollTop = c.scrollHeight;
}

let pendente = { out: null, in: null };
function eventoDoMotor(e) {
  switch (e.e) {
    case "progress":
      status(e.msg); $("barra_cheia").style.width = e.pct + "%"; break;
    case "download": {
      const mb = (x) => (x / 1e6).toFixed(0);
      const v = { what: e.what, got: mb(e.got), total: mb(e.total) };
      vivo("baixando", () => tf(e.total ? "dl_progress" : "dl_progress_nototal", v));
      break;
    }
    case "hardware":
      vivo("hardware", () => tf("hw_detail", {
        hw: t(e.gpu ? "hw_gpu" : "hw_cpu"),
        asr: e.model.startsWith("parakeet") ? "Parakeet" : "Whisper " + e.model, tr: e.translator }));
      break;
    case "virtual_mic":
      $("microfone_virtual").hidden = false;
      vivo("microfone_virtual", () => tf("vmic_choose", { mic: e.mic }) + (e.peer ? tf("vmic_peer", { peer: e.peer }) : ""));
      break;
    case "ready":
      statusT("st_translating", "ok"); fixo("baixando", ""); $("barra").hidden = true; break;
    case "error":
      statusT("st_error", "erro");
      { const p = document.createElement("p"); p.className = "erro-msg"; p.textContent = e.msg; $("conversa").append(p); }
      // o erro também vai para o alto da janela: ao voltar às configurações ele ficava escondido embaixo
      fixo("erro_topo", e.msg); $("erro_topo").hidden = false; $("erro_topo").scrollIntoView({ block: "start" });
      break;
    case "stopped":
      rodando = false; $("iniciar").classList.remove("parar"); $("iniciar").disabled = false;
      aplicarTextos(); statusT("st_stopped");
      // volta às configurações (a conversa e o erro, se houver, continuam visíveis embaixo)
      $("config").hidden = false; $("barra").hidden = true;
      break;
  }
}

function eventoDoMotorInterno(x) {
  // {e:"transcript"|"translation", dir, text}
  if (x.e === "transcript") pendente[x.dir] = x.text;
  else if (x.e === "translation") { adicionarFala(x.dir, pendente[x.dir] || "", x.text); pendente[x.dir] = null; }
  else if (x.e === "error") eventoDoMotor({ e: "error", msg: x.msg });
}

async function iniciarOuParar() {
  if (rodando) {
    $("iniciar").disabled = true; statusT("st_stopping");
    await invoke("parar");
    return;
  }
  await salvar();
  rodando = true;
  $("config").hidden = true; $("painel").hidden = false; $("barra").hidden = false;
  $("conversa").replaceChildren(); $("microfone_virtual").hidden = true; $("erro_topo").hidden = true;
  $("iniciar").classList.add("parar"); aplicarTextos(); statusT("st_starting");
  try { await invoke("iniciar", { config: cfg }); }
  catch (err) { eventoDoMotor({ e: "error", msg: String(err) }); eventoDoMotor({ e: "stopped" }); }
}

function aplicarTema() {
  // só o modo escuro (decisão do produto)
  document.documentElement.dataset.tema = "escuro";
  $("logo").src = "logo-escuro.png";
}

async function main() {
  I18N = await (await fetch("i18n.json")).json();
  ESTADO = await invoke("estado_inicial");
  const sis = ESTADO.idioma_do_sistema;
  // 1ª vez: interface e "você fala" herdam o idioma do sistema
  cfg = Object.assign({
    ui_lang: I18N.strings[sis] ? sis : "en",
    src: I18N.src_langs.includes(sis) ? sis : "en",
    tgt: sis === "en" ? "pt" : "en",
    model: "auto", translator: "auto", monitor: false, headphones: false, bilateral: false,
  }, ESTADO.config || {});

  const ui = $("ui_lang");
  for (const c of Object.keys(I18N.strings)) ui.append(opcao(c, I18N.native_names[c] || c));
  ui.value = cfg.ui_lang;
  ui.onchange = () => { cfg.ui_lang = ui.value; aplicarTextos(); preencherIdiomas(); preencherDispositivos(); salvar(); };

  for (const id of ["monitor", "headphones", "bilateral"]) $(id).checked = !!cfg[id];
  $("model").value = cfg.model; $("translator").value = cfg.translator;
  // opção salva que não existe mais nesta versão (ex.: "Parakeet v3"): volta ao automático
  if (!$("model").value) { $("model").value = "auto"; cfg.model = "auto"; }
  if (!$("translator").value) { $("translator").value = "auto"; cfg.translator = "auto"; }
  vivo("hardware", () => t(ESTADO.placa_de_video ? "hw_gpu_found" : "hw_no_gpu"));
  aplicarTemaInicial();
  aplicarTextos(); preencherIdiomas(); preencherDispositivos();

  for (const id of ["src", "tgt", "bilateral"]) $(id).addEventListener("change", () => { verificarIdiomas(); salvar(); });
  for (const id of ["mic", "output", "monitor", "headphones", "model", "translator"]) $(id).addEventListener("change", salvar);
  // sem fone e com tradução tocando na caixa de som, a trava de eco deixa o microfone surdo
  const avisoEco = () => { $("aviso_eco").hidden = $("headphones").checked || !($("monitor").checked || $("bilateral").checked); };
  for (const id of ["monitor", "headphones", "bilateral"]) $(id).addEventListener("change", avisoEco);
  avisoEco();
  $("iniciar").onclick = iniciarOuParar;

  await listen("praxis", (ev) => {
    const e = ev.payload;
    if (e.e === "engine") eventoDoMotorInterno(e.ev);
    else eventoDoMotor(e);
  });
  if (await invoke("modo_qa")) iniciarOuParar();   // verificação de qualidade automática
  verificarAtualizacao();
}

// Versão nova publicada: avisa no topo; o botão pede a senha do sistema e atualiza.
async function verificarAtualizacao() {
  let r;
  try { r = await invoke("verificar_atualizacao"); } catch { return; }
  if (!r || !r.nova) return;
  vivo("atualizacao_texto", () => tf("upd_available", { new: r.nova, cur: r.atual }));
  $("atualizacao").hidden = false;
  $("atualizar").onclick = async () => {
    $("atualizar").disabled = true;
    vivo("atualizacao_texto", () => t("upd_running"));
    try { await invoke("atualizar"); }
    catch (e) { fixo("atualizacao_texto", String(e)); $("atualizar").disabled = false; }
  };
}

function aplicarTemaInicial() {
  aplicarTema();
}

// sem o i18n.json carregado não há tradução: cai no português
main().catch((e) => { document.body.textContent = I18N ? tf("err_open", { err: e }) : "Erro ao abrir o Praxis: " + e; });
