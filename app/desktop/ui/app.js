// Praxis — janela. Toda a lógica está no motor; aqui só a interface.
const { invoke } = window.__TAURI__.core;
const { listen } = window.__TAURI__.event;

const $ = (id) => document.getElementById(id);
let I18N = null;      // textos da interface em 14 idiomas (os mesmos do Praxis em Python)
let ESTADO = null;    // vindo do motor: dispositivos, idiomas liberados, placa de vídeo
let cfg = {};
let rodando = false;

const t = (k) => (I18N.strings[cfg.ui_lang] || I18N.strings.pt)[k] || I18N.strings.pt[k] || k;
const nomeIdioma = (c) => ((I18N.lang_names[cfg.ui_lang] || {})[c]) || I18N.native_names[c] || c;

function aplicarTextos() {
  document.querySelectorAll("[data-t]").forEach((el) => (el.textContent = t(el.dataset.t)));
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
    const marca = i.liberado ? "" : "  — indisponível neste computador";
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
    const v = m.includes("ultra") ? "ultra" : m.includes("-ja-") ? "japonês" : m.includes("v2") ? "v2 (inglês)" : "v3";
    return "Parakeet " + v;
  }
  return "Whisper " + m;
}

function diagnostico() {
  const info = (c) => ESTADO.idiomas.find((i) => i.codigo === c);
  const linha = (c) => {
    const i = info(c);
    if (!i) return "";
    const erro = i.erro == null ? "sem medição" : `erra cerca de ${(i.erro * 100).toFixed(1).replace(".", ",")}% das palavras`;
    return `${nomeModelo(i.modelo)} para ${nomeIdioma(c)}: ${erro}`;
  };
  const partes = [linha($("src").value)];
  if ($("bilateral").checked) partes.push(linha($("tgt").value));
  $("diagnostico").textContent = partes.filter(Boolean).join(" · ");
}

function verificarIdiomas() {
  diagnostico();
  const s = $("src").value, d = $("tgt").value;
  const info = (c) => ESTADO.idiomas.find((i) => i.codigo === c) || { liberado: true };
  let msg = "";
  if (s === d) msg = "Escolha idiomas diferentes para falar e para a tradução.";
  else if (!info(s).liberado) msg = info(s).motivo;
  else if ($("bilateral").checked && !info(d).liberado) msg = "No bilateral a outra pessoa fala " + nomeIdioma(d) + ": " + info(d).motivo;
  const aviso = $("aviso_idioma");
  aviso.hidden = !msg; aviso.textContent = msg;
  $("iniciar").disabled = !rodando && !!msg;
}

function preencherDispositivos() {
  const padrao = t("lbl_sys_default");
  for (const [id, lista] of [["mic", ESTADO.entradas], ["output", ESTADO.saidas]]) {
    const sel = $(id);
    sel.replaceChildren(opcao("", padrao));
    for (const n of lista) if (!/^Praxis_/.test(n)) sel.append(opcao(n, n));
    sel.value = cfg[id] || "";
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

function status(texto, tipo = "") {
  $("status_texto").textContent = texto;
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
      $("baixando").textContent = e.total
        ? `Baixando ${e.what}: ${mb(e.got)} de ${mb(e.total)} MB (só na primeira vez)`
        : `Baixando ${e.what}: ${mb(e.got)} MB (só na primeira vez)`;
      break;
    }
    case "hardware":
      $("hardware").textContent = (e.gpu ? "Placa de vídeo NVIDIA" : "Sem placa de vídeo: processador") +
        ` · reconhecimento de fala ${e.model.startsWith("parakeet") ? "Parakeet" : "Whisper " + e.model} · tradutor ${e.translator}`;
      break;
    case "virtual_mic":
      $("microfone_virtual").hidden = false;
      $("microfone_virtual").textContent = `No seu app de chamada, escolha "${e.mic}" como microfone.` +
        (e.peer ? ` E mande a saída de som do app para "${e.peer}".` : "");
      break;
    case "ready":
      status("Traduzindo", "ok"); $("baixando").textContent = ""; $("barra").hidden = true; break;
    case "error":
      status("Erro", "erro");
      { const p = document.createElement("p"); p.className = "erro-msg"; p.textContent = e.msg; $("conversa").append(p); }
      break;
    case "stopped":
      rodando = false; $("iniciar").classList.remove("parar"); $("iniciar").disabled = false;
      aplicarTextos(); status("Parado");
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
    $("iniciar").disabled = true; status("Parando…");
    await invoke("parar");
    return;
  }
  await salvar();
  rodando = true;
  $("config").hidden = true; $("painel").hidden = false; $("barra").hidden = false;
  $("conversa").replaceChildren(); $("microfone_virtual").hidden = true;
  $("iniciar").classList.add("parar"); aplicarTextos(); status("Iniciando…");
  try { await invoke("iniciar", { config: cfg }); }
  catch (err) { eventoDoMotor({ e: "error", msg: String(err) }); eventoDoMotor({ e: "stopped" }); }
}

function aplicarTema() {
  const escuro = cfg.theme ? cfg.theme === "escuro" : matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.dataset.tema = escuro ? "escuro" : "claro";
  $("logo").src = escuro ? "logo-escuro.png" : "logo.png";
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
  $("hardware").textContent = ESTADO.placa_de_video ? "Placa de vídeo NVIDIA encontrada" : "Sem placa de vídeo compatível: o Praxis usa o processador";
  aplicarTemaInicial();
  aplicarTextos(); preencherIdiomas(); preencherDispositivos();

  for (const id of ["src", "tgt", "bilateral"]) $(id).addEventListener("change", () => { verificarIdiomas(); salvar(); });
  for (const id of ["mic", "output", "monitor", "headphones", "model", "translator"]) $(id).addEventListener("change", salvar);
  $("iniciar").onclick = iniciarOuParar;
  $("tema").onclick = () => { cfg.theme = document.documentElement.dataset.tema === "escuro" ? "claro" : "escuro"; aplicarTema(); salvar(); };

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
  $("atualizacao_texto").textContent = `Versão ${r.nova} disponível (você tem a ${r.atual}).`;
  $("atualizacao").hidden = false;
  $("atualizar").onclick = async () => {
    $("atualizar").disabled = true;
    $("atualizacao_texto").textContent = "Atualizando… (o sistema vai pedir a sua senha)";
    try { await invoke("atualizar"); }
    catch (e) { $("atualizacao_texto").textContent = String(e); $("atualizar").disabled = false; }
  };
}

function aplicarTemaInicial() {
  aplicarTema();
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { if (!cfg.theme) aplicarTema(); });
}

main().catch((e) => { document.body.textContent = "Erro ao abrir o Praxis: " + e; });
