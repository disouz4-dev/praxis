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
    : !(ESTADO.voz && ESTADO.voz.existe) ? t("warn_need_voice")
    : !ESTADO.voz.clonada ? t("warn_cloning")
    : $("voz_modelo").value === "leve" && !ESTADO.voz.clone_leve ? t("warn_cloning")
    : !info(s).liberado ? info(s).motivo
    : bi && !info(d).liberado ? tf("warn_bilateral", { lang: nomeIdioma(d), reason: info(d).motivo })
    : bi && ESTADO.sistema === "windows" && !$("peer_app").value ? t("warn_peer_app")
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

// Bilateral: de qual app vem a outra pessoa. Com um app escolhido o Praxis pega o som dele
// sozinho; sem escolha (Linux/macOS), o usuário manda a saída do app para o Praxis Speaker.
function preencherApps(lista) {
  const sel = $("peer_app");
  const atual = sel.value || cfg.peer_app || "";
  sel.replaceChildren(opcao("", t(ESTADO.sistema === "windows" ? "opt_peer_none" : "opt_peer_manual")));
  const nomes = new Map(lista.map((a) => [a.id, a.name]));
  if (cfg.peer_app && !nomes.has(cfg.peer_app)) nomes.set(cfg.peer_app, cfg.peer_app_nome || cfg.peer_app);
  for (const [id, nome] of nomes) { const o = opcao(id, nome); o.dataset.nome = nome; sel.append(o); }
  sel.value = nomes.has(atual) ? atual : "";
  dicaBilateral();
}

function dicaBilateral() {
  const sel = $("peer_app");
  $("bilateral_opcoes").hidden = !$("bilateral").checked;
  vivo("dica_peer_app", () => sel.value ? tf("hint_peer_app_auto", { app: sel.selectedOptions[0].textContent })
    : t(ESTADO.sistema === "windows" ? "hint_peer_win" : "hint_peer_manual"));
  // só legenda: a voz original já toca inteira. No Windows a voz original sai do próprio app,
  // sempre (no mínimo 5%): só o volume dela é escolhido.
  const win = ESTADO.sistema === "windows", legenda = $("peer_legenda").checked;
  $("original_linha").hidden = legenda || win;
  $("original_volume_linha").hidden = legenda || (!win && !$("original").checked);
  $("original_volume_valor").textContent = $("original_volume").value + "%";
}

async function atualizarApps() {
  try { preencherApps(await invoke("apps_com_som")); } catch { /* lista fica como está */ }
}

// Monitor de erros: o usuário vê tudo o que vai no relato antes de abrir o GitHub.
async function abrirRelatorio() {
  let r = "";
  try { r = await invoke("relatorio_de_erros"); } catch (err) { r = String(err); }
  $("relatorio_texto").textContent = r;
  $("relatorio_descricao").value = "";
  $("relatorio").showModal();
}

function textoDoRelato() {
  const o_que = $("relatorio_descricao").value.trim();
  return (o_que ? "### O que eu estava fazendo\n" + o_que + "\n\n" : "") + $("relatorio_texto").textContent;
}

// Monitoria (o botão da versão antiga): ouvir a própria tradução numa saída do computador
function aplicarMonitor() {
  const on = $("monitor").checked;
  vivo("monitor_btn", () => t(on ? "mon_on" : "mon_off"));
  $("monitor_btn").setAttribute("aria-pressed", String(on));
  $("monitor_btn").classList.toggle("ligado", on);
  $("saida_linha").hidden = !on;
  // com a tradução em andamento, vale na hora (sem reiniciar)
  if (rodando) invoke("definir_monitor", { ligado: on }).catch(() => {});
}

// A conversa fica sempre na tela principal (logo abaixo dos idiomas e da voz)
async function abrirPainel() {
  $("painel").hidden = false;
}

// Voz da tradução: o clone fiel na placa de vídeo (OmniVoice) quando há, ou o clone leve
function montarVozes() {
  const v = ESTADO.voz || {};
  const opcoes = [];
  if (v.omnivoice) opcoes.push(["omni", t("voice_model_omni")]);
  opcoes.push(["leve", t("voice_model_light")]);
  const atual = cfg.voz_modelo && opcoes.some(([k]) => k === cfg.voz_modelo) ? cfg.voz_modelo : opcoes[0][0];
  $("voz_modelo").replaceChildren(...opcoes.map(([k, n]) => { const o = document.createElement("option"); o.value = k; o.textContent = n; return o; }));
  $("voz_modelo").value = atual;
  vivo("voz_resumo", () => !v.existe ? t("voice_missing_main") : "");
}

// Seu computador (em Configurações): o hardware identificado pelo próprio Praxis e o uso de cada peça
let HARDWARE = null;
async function atualizarUso() {
  if (!$("configuracoes").open) return;
  if (!HARDWARE) { try { HARDWARE = await invoke("hardware"); } catch { return; } }
  let u;
  try { u = await invoke("uso_do_sistema"); } catch { return; }
  const gb = (mb) => (mb / 1024).toLocaleString(cfg.ui_lang, { maximumFractionDigits: mb >= 10240 ? 0 : 1 });
  const linha = (rotulo, nome, detalhe, pct, texto) => {
    const d = document.createElement("div"); d.className = "uso-linha";
    d.innerHTML = '<span class="uso-rotulo"></span><span class="uso-nome"></span><span class="uso-detalhe"></span>' +
      '<span class="uso-barra"><i></i></span><span class="uso-pct"></span>';
    d.querySelector(".uso-rotulo").textContent = rotulo;
    d.querySelector(".uso-nome").textContent = nome;
    d.querySelector(".uso-detalhe").textContent = detalhe;
    const p = pct ?? 0;
    d.querySelector(".uso-barra i").style.transform = `scaleX(${Math.min(1, p / 100)})`;
    d.querySelector(".uso-barra").className = "uso-barra" + (pct == null ? " repouso" : p >= 85 ? " alto" : p >= 60 ? " medio" : "");
    d.querySelector(".uso-pct").textContent = texto ?? `${Math.round(p)}%`;
    return d;
  };
  const h = HARDWARE, cpu = h.processador || {}, mem = h.memoria || {};
  const linhas = [linha(t("hw_cpu_label"), cpu.nome || "?", tf("hw_cores", { f: cpu.nucleos_fisicos ?? "?", l: cpu.nucleos ?? "?" }), u.cpu)];
  for (const g of u.placas || []) {
    const info = (h.placas || []).find((p) => p.nome === g.nome) || {};
    linhas.push(linha(t("hw_gpu_label"), g.nome, info.memoria_mb ? `${gb(info.memoria_mb)} GB` : "", g.uso, g.uso == null ? t("usage_gpu_idle") : null));
  }
  if (!(u.placas || []).length) linhas.push(linha(t("hw_gpu_label"), t("hw_no_gpu"), t("hw_no_gpu_hint"), null, "—"));
  const memDet = [mem.tipo, mem.velocidade_mhz ? `${mem.velocidade_mhz} MHz` : null, mem.fabricante].filter(Boolean).join(" · ");
  linhas.push(linha(t("hw_mem_label"), `${gb(u.memoria_total_mb)} GB`, memDet,
    100 * u.memoria_usada_mb / Math.max(1, u.memoria_total_mb), tf("hw_mem_used", { u: gb(u.memoria_usada_mb) })));
  $("uso").replaceChildren(...linhas);
  fixo("computador_sistema", h.sistema || "");
}

// "Quem é traduzido?": Só eu / Nós dois liga o modo bilateral (a caixa escondida #bilateral)
function aplicarModo() {
  $("modo_dois").checked = $("bilateral").checked;
  $("modo_eu").checked = !$("bilateral").checked;
}

function escolherModo(dois) {
  if ($("bilateral").checked === dois) return;
  $("bilateral").checked = dois;
  $("bilateral").dispatchEvent(new Event("change"));
}

// ⇄ troca os idiomas de lado (o que eu falo passa a ser o que eles ouvem e vice-versa)
function trocarIdiomas() {
  const s = $("src").value, d = $("tgt").value;
  const podeSrc = [...$("src").options].some((o) => o.value === d && !o.disabled);
  const podeTgt = [...$("tgt").options].some((o) => o.value === s);
  if (!podeSrc || !podeTgt) { vivo("aviso_idioma", () => t("warn_swap")); $("aviso_idioma").hidden = false; return; }
  $("src").value = d; $("tgt").value = s;
  verificarIdiomas(); salvar();
}

// Teste do microfone: a barra mostra o volume da voz antes de começar a traduzir
let testandoMic = false;
async function testarMicrofone(ligar = !testandoMic) {
  if (!ligar) {
    testandoMic = false;
    try { await invoke("parar_teste_microfone"); } catch { /* já parou */ }
    $("medidor").hidden = true; $("dica_medidor").hidden = true;
    document.querySelectorAll(".medidor i").forEach((b) => (b.style.transform = "scaleX(0)"));
    $("testar_mic").textContent = t("btn_test_mic");
    return;
  }
  try { await invoke("testar_microfone", { nome: $("mic").value || null }); }
  catch (e) { fixo("erro_texto", String(e)); $("erro_topo").hidden = false; return; }
  testandoMic = true;
  $("medidor").hidden = false; $("dica_medidor").hidden = false;
  $("testar_mic").textContent = t("btn_test_stop");
}

function mostrarNivel(n) {
  // todas as barras de nível visíveis (a da tela e a do tutorial)
  document.querySelectorAll(".medidor i").forEach((b) => (b.style.transform = `scaleX(${n.toFixed(3)})`));
}

// ── Voz do usuário (obrigatória: a tradução sai na voz dele) ─────────────────
let gravando = false;
function textoLeitura() {
  const tx = I18N.textos_voz || {};
  return tx[$("src").value] || tx[cfg.ui_lang] || tx.en || "";
}

function montarGravador(c, comExplicacao) {
  const g = document.createElement("div"); g.className = "gravador";
  g.innerHTML = '<p class="grav-explica"></p><p class="grav-rotulo"></p><blockquote class="texto-leitura"></blockquote>' +
    '<div class="grav-linha"><button type="button" class="gravar"></button><span class="grav-tempo">0:00</span></div>' +
    '<div class="medidor grande voz"><i></i></div><p class="grav-resultado" role="status" aria-live="polite"></p>';
  g.querySelector(".grav-explica").textContent = comExplicacao ? t("tutvoz_body") : "";
  g.querySelector(".grav-explica").hidden = !comExplicacao;
  g.querySelector(".grav-rotulo").textContent = t("rec_read");
  g.querySelector(".texto-leitura").textContent = textoLeitura();
  const botao = g.querySelector(".gravar");
  const rotulo = () => { botao.textContent = t(gravando ? "btn_rec_stop" : "btn_rec_start"); botao.classList.toggle("ativo", gravando); };
  rotulo();
  botao.onclick = async () => {
    const res = g.querySelector(".grav-resultado");
    if (!gravando) {
      if (testandoMic) await testarMicrofone(false);
      botao.disabled = true; // um segundo clique enquanto o microfone abre não grava duas vezes
      try { await invoke("gravar_voz", { nome: $("mic").value || null }); }
      catch (e) { res.textContent = String(e); return; }
      finally { botao.disabled = false; }
      gravando = true; res.textContent = ""; rotulo();
      return;
    }
    gravando = false; rotulo();
    document.querySelectorAll(".medidor.voz i").forEach((b) => (b.style.transform = "scaleX(0)"));
    let r;
    try { r = await invoke("parar_gravacao_voz"); } catch (e) { res.textContent = String(e); return; }
    const seg = (r.fala || 0).toLocaleString(cfg.ui_lang, { maximumFractionDigits: 0 });
    res.textContent = tf(r.ok ? "rec_saved" : "rec_short", { s: seg });
    res.className = "grav-resultado " + (r.ok ? "ok" : "aviso");
    if (r.ok) { CLONAGEM.fracao = 0; CLONAGEM.erro = ""; }
    try { ESTADO.voz = await invoke("estado_voz"); } catch { /* fica o estado anterior */ }
    atualizarVoz(); verificarIdiomas();
  };
  c.append(g);
}

async function cancelarGravacao() {
  if (!gravando) return;
  gravando = false;
  try { await invoke("parar_gravacao_voz"); ESTADO.voz = await invoke("estado_voz"); } catch { /* nada a salvar */ }
  atualizarVoz();
}

// clonagem da voz (feita pelo Praxis logo depois da gravação)
const CLONAGEM = { fracao: 0, texto: "", erro: "" };
async function ouvirClonagem() {
  await listen("clonagem", async (ev) => {
    const c = ev.payload;
    if (c.erro) { CLONAGEM.erro = c.erro; }
    else if (c.fim) { CLONAGEM.fracao = 1; CLONAGEM.erro = ""; try { ESTADO.voz = await invoke("estado_voz"); } catch { /* fica */ } }
    else { CLONAGEM.fracao = c.fracao; CLONAGEM.texto = c.texto; CLONAGEM.erro = ""; }
    atualizarVoz(); verificarIdiomas();
  });
}

function atualizarVoz() {
  const v = ESTADO.voz || {};
  if ($("voz_modelo")) montarVozes();
  vivo("voz_estado", () => !v.existe ? t("voice_missing")
    : v.clonada ? tf("voice_cloned", { s: Math.round(v.segundos || 0) })
    : CLONAGEM.erro ? tf("voice_clone_error", { e: CLONAGEM.erro })
    : tf("voice_cloning", { p: Math.round((CLONAGEM.fracao || 0) * 100) }));
  $("voz_estado").className = "voz-estado " + (!v.existe ? "falta" : v.clonada ? "ok" : CLONAGEM.erro ? "falta" : "clonando");
  $("voz_clonar_btn").hidden = !v.existe || (!v.clonada && !CLONAGEM.erro);
  vivo("voz_gravar_btn", () => t(v.existe ? "btn_rerecord_voice" : "btn_record_voice"));
  // no tutorial, o passo da voz só segue depois de gravar
  if ($("tutorial").open && PASSOS[passoAtual]?.k === "tutvoz") $("tut_seguir").disabled = !v.existe;
  verificarIdiomas();
}

function abrirGravador() {
  const c = $("grav_conteudo"); c.replaceChildren(); montarGravador(c, true);
  $("gravador").showModal();
}

// ── Tutorial ─────────────────────────────────────────────────────────────────
// Obrigatório na primeira vez (com "Pular tutorial"); de novo em ⓘ Sobre. Os campos dos
// passos são cópias ligadas aos de verdade: mudar aqui muda na tela principal.
function copiaSelect(id) {
  const orig = $(id), sel = document.createElement("select");
  sel.innerHTML = orig.innerHTML; sel.value = orig.value;
  sel.onchange = () => { orig.value = sel.value; orig.dispatchEvent(new Event("change")); };
  return sel;
}

function copiaCaixa(id, chave) {
  const lab = document.createElement("label"); lab.className = "chave";
  const c = document.createElement("input"); c.type = "checkbox"; c.checked = $(id).checked;
  c.onchange = () => { $(id).checked = c.checked; $(id).dispatchEvent(new Event("change")); };
  const sp = document.createElement("span"); sp.textContent = t(chave);
  lab.append(c, sp);
  return lab;
}

function campo(chave, el) {
  const lab = document.createElement("label"); lab.className = "campo";
  const sp = document.createElement("span"); sp.textContent = t(chave);
  lab.append(sp, el);
  return lab;
}

const PASSOS = [
  { k: "tut1" },
  { k: "tut2", montar: (c) => {
      const par = document.createElement("div"); par.className = "par tut-par";
      const eu = campo("lbl_you_speak", copiaSelect("src")); eu.classList.add("lado", "eu");
      const eles = campo("lbl_they_hear", copiaSelect("tgt")); eles.classList.add("lado", "eles");
      par.append(eu, eles); c.append(par);
    } },
  { k: "tut3", montar: (c) => {
      c.append(campo("lbl_your_mic", copiaSelect("mic")));
      const m = document.createElement("div"); m.className = "medidor grande"; m.innerHTML = "<i></i>"; c.append(m);
      c.append(copiaCaixa("headphones", "tut3_fone"));
      c.querySelector("select").addEventListener("change", () => testarMicrofone(true));
    }, entrar: () => testarMicrofone(true), sair: () => testarMicrofone(false) },
  { k: "tutvoz", montar: (c) => montarGravador(c, false), sair: () => cancelarGravacao() },
  { k: "tut4", montar: (c) => { const p = document.createElement("p"); p.className = "praxis-mic grande"; p.innerHTML = "<b>Praxis Mic</b>"; c.append(p); } },
  { k: "tut5", montar: (c) => {
      const f = document.createElement("div"); f.className = "modo";
      for (const [dois, ch, dica] of [[false, "opt_only_me", "opt_only_me_hint"], [true, "opt_both", "opt_both_hint"]]) {
        const lab = document.createElement("label"); lab.className = "opcao-modo";
        const r = document.createElement("input"); r.type = "radio"; r.name = "tut_modo"; r.checked = $("bilateral").checked === dois;
        r.onchange = () => escolherModo(dois);
        const sp = document.createElement("span"); sp.innerHTML = "<b></b><small></small>";
        sp.querySelector("b").textContent = t(ch); sp.querySelector("small").textContent = t(dica);
        lab.append(r, sp); f.append(lab);
      }
      c.append(f);
    } },
  { k: "tut6" },
];
let passoAtual = 0;

function mostrarPasso(i) {
  PASSOS[passoAtual]?.sair?.();
  passoAtual = i;
  const p = PASSOS[i];
  vivo("tut_passo", () => tf("tut_step", { n: i + 1, total: PASSOS.length }));
  vivo("tut_titulo", () => tf(p.k + "_title", { mic: "Praxis Mic" }));
  vivo("tut_texto", () => tf(p.k + "_body", { mic: "Praxis Mic" }));
  const c = $("tut_conteudo"); c.replaceChildren(); p.montar?.(c);
  $("tut_pontos").replaceChildren(...PASSOS.map((_, j) => { const d = document.createElement("i"); if (j === i) d.className = "atual"; return d; }));
  $("tut_voltar").hidden = i === 0;
  $("tut_seguir").textContent = t(i === PASSOS.length - 1 ? "tut_done" : i === 0 ? "tut_start" : "tut_next");
  $("tut_pular").hidden = i === PASSOS.length - 1;
  $("tut_seguir").disabled = p.k === "tutvoz" && !(ESTADO.voz && ESTADO.voz.existe);
  p.entrar?.();
  $("tut_seguir").focus();
}

function abrirTutorial() {
  $("sobre").open && $("sobre").close();
  $("tutorial").showModal();
  mostrarPasso(0);
}

function fecharTutorial() {
  PASSOS[passoAtual]?.sair?.();
  $("tutorial").close();
  cfg.tutorial_feito = true; salvar();
  $("iniciar").focus();
}

function coletar() {
  return {
    ...cfg,
    src: $("src").value, tgt: $("tgt").value,
    mic: $("mic").value || null, output: $("output").value || null,
    monitor: $("monitor").checked, headphones: $("headphones").checked,
    bilateral: $("bilateral").checked,
    model: $("model").value, translator: $("translator").value,
    voz_modelo: $("voz_modelo").value, omnivoice: $("voz_modelo").value === "omni",
    peer_app: $("peer_app").value || null,
    peer_app_nome: $("peer_app").selectedOptions[0]?.dataset.nome || null,
    peer_voice: !$("peer_legenda").checked,
    original_nivel: +$("original_volume").value,
    original_volume: ($("original").checked || ESTADO.sistema === "windows") ? +$("original_volume").value / 100 : 0,
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

// Conversa como num aplicativo de mensagens: a minha fala em balões à esquerda, a da outra
// pessoa à direita. A linha de cima fica sempre no meu idioma. Os pedaços da tradução
// simultânea entram no mesmo balão até a frase terminar ou haver uma pausa.
let ultimoBalao = null;
function adicionarFala(dir, original, traducao) {
  const c = $("conversa");
  const agora = Date.now();
  const meu = dir === "out";
  const [cima, baixo] = meu ? [original, traducao] : [traducao, original];
  const u = ultimoBalao;
  if (u && u.dir === dir && agora - u.t < 2500 && !/[.?!…]$/.test(u.cima.textContent.trim())) {
    u.cima.textContent += " " + cima;
    u.baixo.textContent += " " + baixo;
    u.t = agora;
  } else {
    const div = document.createElement("div");
    div.className = "fala " + dir;
    div.innerHTML = '<div class="rotulo"><span class="quem"></span><span class="hora"></span></div><div class="cima"></div><div class="baixo"></div>';
    div.querySelector(".quem").dataset.t = meu ? "lbl_you" : "lbl_other";
    div.querySelector(".quem").textContent = t(meu ? "lbl_you" : "lbl_other");
    div.querySelector(".hora").textContent = new Date().toLocaleTimeString(cfg.ui_lang, { hour: "2-digit", minute: "2-digit" });
    div.querySelector(".cima").textContent = cima;
    div.querySelector(".baixo").textContent = baixo;
    c.append(div);
    ultimoBalao = { dir, t: agora, cima: div.querySelector(".cima"), baixo: div.querySelector(".baixo") };
  }
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
      fixo("erro_texto", e.msg); $("erro_topo").hidden = false; $("erro_topo").scrollIntoView({ block: "start" });
      break;
    case "stopped":
      rodando = false; $("iniciar").classList.remove("parar"); $("iniciar").disabled = false;
      aplicarTextos(); statusT("st_stopped");
      // as configurações voltam a responder; o painel fica aberto com a conversa (✕ fecha)
      $("config").inert = false; $("config").hidden = false; $("barra").hidden = true; document.body.classList.remove("rodando");
      $("output").disabled = false; $("voz_modelo").disabled = false;
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
  if (testandoMic) await testarMicrofone(false);
  await salvar();
  rodando = true;
  $("config").inert = true; $("barra").hidden = false; document.body.classList.add("rodando"); abrirPainel();
  $("configuracoes").open && $("configuracoes").close();
  $("voz_modelo").disabled = true;
  $("output").disabled = true; // a saída da monitoria é aberta ao começar; troca só parando
  $("conversa").replaceChildren(); ultimoBalao = null; $("microfone_virtual").hidden = true; $("erro_topo").hidden = true;
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
  ui.onchange = () => {
    cfg.ui_lang = ui.value; aplicarTextos(); preencherIdiomas(); preencherDispositivos();
    preencherApps([...$("peer_app").options].filter((o) => o.value).map((o) => ({ id: o.value, name: o.dataset.nome })));
    salvar();
  };

  for (const id of ["monitor", "headphones", "bilateral"]) $(id).checked = !!cfg[id];
  $("model").value = cfg.model; $("translator").value = cfg.translator;
  // opção salva que não existe mais nesta versão (ex.: "Parakeet v3"): volta ao automático
  if (!$("model").value) { $("model").value = "auto"; cfg.model = "auto"; }
  if (!$("translator").value) { $("translator").value = "auto"; cfg.translator = "auto"; }
  vivo("hardware", () => t(ESTADO.placa_de_video ? "hw_gpu_found" : "hw_no_gpu"));
  aplicarTemaInicial();
  $("original").checked = (cfg.original_volume || 0) > 0;
  $(cfg.peer_voice === false ? "peer_legenda" : "peer_voz").checked = true;
  $("original_volume").value = cfg.original_nivel || 15;
  aplicarTextos(); preencherIdiomas(); preencherDispositivos(); preencherApps(ESTADO.apps || []); verificarIdiomas();

  for (const id of ["src", "tgt", "bilateral"]) $(id).addEventListener("change", () => { verificarIdiomas(); salvar(); });
  for (const id of ["mic", "output", "monitor", "headphones", "model", "translator"]) $(id).addEventListener("change", salvar);
  $("bilateral").addEventListener("change", () => { dicaBilateral(); if ($("bilateral").checked) atualizarApps(); });
  $("peer_app").addEventListener("change", () => { dicaBilateral(); verificarIdiomas(); salvar(); });
  $("atualizar_apps").onclick = atualizarApps;
  for (const id of ["original", "original_volume", "peer_voz", "peer_legenda"]) $(id).addEventListener("input", () => { dicaBilateral(); salvar(); });
  // sem fone e com tradução tocando na caixa de som, a trava de eco deixa o microfone surdo
  const avisoEco = () => { $("aviso_eco").hidden = $("headphones").checked || !($("monitor").checked || $("bilateral").checked); };
  for (const id of ["monitor", "headphones", "bilateral"]) $(id).addEventListener("change", avisoEco);
  avisoEco();
  $("iniciar").onclick = iniciarOuParar;
  $("trocar").onclick = trocarIdiomas;
  $("monitor_btn").onclick = () => { $("monitor").checked = !$("monitor").checked; $("monitor").dispatchEvent(new Event("change")); };
  $("monitor").addEventListener("change", aplicarMonitor);
  aplicarMonitor();
  $("config_abrir").onclick = () => { $("configuracoes").showModal(); atualizarUso(); };
  $("config_fechar").onclick = () => $("configuracoes").close();
  $("voz_modelo").addEventListener("change", () => {
    cfg.voz_modelo = $("voz_modelo").value; salvar();
    // a voz leve é um ajuste fino feito no processador: se ainda não existe, começa agora
    if (cfg.voz_modelo === "leve" && ESTADO.voz?.existe && !ESTADO.voz.clone_leve) {
      CLONAGEM.fracao = 0; CLONAGEM.erro = ""; ESTADO.voz.clonada = false; atualizarVoz();
      invoke("clonar_voz").catch((e) => { CLONAGEM.erro = String(e); atualizarVoz(); });
    }
    verificarIdiomas();
  });
  montarVozes();
  $("conversa").dataset.vazio = t("chat_empty");
  atualizarUso(); setInterval(atualizarUso, 2000);
  $("modo_eu").onchange = () => escolherModo(false);
  $("modo_dois").onchange = () => escolherModo(true);
  $("bilateral").addEventListener("change", aplicarModo);
  aplicarModo();
  $("testar_mic").onclick = () => testarMicrofone();
  $("mic").addEventListener("change", () => { if (testandoMic) testarMicrofone(true); });
  await listen("nivel_mic", (ev) => { if (ev.payload.parou) { if (testandoMic) testarMicrofone(false); } else mostrarNivel(ev.payload.nivel); });
  $("tut_seguir").onclick = () => (passoAtual < PASSOS.length - 1 ? mostrarPasso(passoAtual + 1) : fecharTutorial());
  $("tut_voltar").onclick = () => mostrarPasso(passoAtual - 1);
  $("tut_pular").onclick = fecharTutorial;
  // Esc não fecha o tutorial (ele é obrigatório na primeira vez): use "Pular tutorial"
  $("tutorial").addEventListener("cancel", (ev) => ev.preventDefault());
  $("sobre_tutorial").onclick = abrirTutorial;
  $("voz_gravar_btn").onclick = abrirGravador;
  $("grav_fechar").onclick = async () => { await cancelarGravacao(); $("gravador").close(); };
  $("gravador").addEventListener("cancel", (ev) => { ev.preventDefault(); $("grav_fechar").click(); });
  await listen("gravacao_voz", (ev) => {
    const { nivel, segundos, fim } = ev.payload;
    document.querySelectorAll(".medidor.voz i").forEach((b) => (b.style.transform = `scaleX(${nivel.toFixed(3)})`));
    const m = Math.floor(segundos / 60), sg = Math.floor(segundos % 60);
    document.querySelectorAll(".grav-tempo").forEach((e) => (e.textContent = `${m}:${String(sg).padStart(2, "0")}`));
    // o motor parou de gravar (90 s ou o microfone sumiu): termina e guarda como se a pessoa clicasse em Parar
    if (gravando && (fim || segundos >= 90)) document.querySelector(".gravar.ativo")?.click();
  });
  await ouvirClonagem();
  // voz gravada mas ainda não clonada (ou gravação nova): o Praxis clona sozinho
  if (ESTADO.voz && ESTADO.voz.existe && !ESTADO.voz.clonada) invoke("clonar_voz").catch(() => {});
  $("voz_clonar_btn").onclick = () => { CLONAGEM.erro = ""; CLONAGEM.fracao = 0; ESTADO.voz.clonada = false; atualizarVoz(); verificarIdiomas(); invoke("clonar_voz").catch((e) => { CLONAGEM.erro = String(e); atualizarVoz(); }); };
  atualizarVoz();
  $("relatar").onclick = $("erro_relatar").onclick = abrirRelatorio;
  $("sobre_abrir").onclick = abrirSobre;
  $("sobre_fechar").onclick = () => $("sobre").close();
  $("sobre_verificar").onclick = verificarNoSobre;
  $("sobre_relatar").onclick = (ev) => { ev.preventDefault(); $("sobre").close(); abrirRelatorio(); };
  document.querySelectorAll("#sobre [data-link]").forEach((a) => {
    a.onclick = (ev) => { ev.preventDefault(); invoke("abrir_link", { url: a.dataset.link }); };
  });
  $("relatorio_fechar").onclick = () => $("relatorio").close();
  $("relatorio_copiar").onclick = async () => {
    try { await navigator.clipboard.writeText(textoDoRelato()); fixo("relatorio_copiar", t("report_copied")); } catch { /* sem área de transferência */ }
    setTimeout(() => { $("relatorio_copiar").textContent = t("btn_copy"); }, 1500);
  };
  $("relatorio_abrir").onclick = async () => {
    try { await invoke("abrir_relato", { corpo: textoDoRelato() }); $("relatorio").close(); }
    catch (err) { fixo("relatorio_texto", String(err)); }
  };

  await listen("praxis", (ev) => {
    const e = ev.payload;
    if (e.e === "engine") eventoDoMotorInterno(e.ev);
    else eventoDoMotor(e);
  });
  if (await invoke("modo_qa")) iniciarOuParar();   // verificação de qualidade automática
  else if (!cfg.tutorial_feito) abrirTutorial();    // primeira vez: tutorial obrigatório
  verificarAtualizacao();
}

// Versão nova publicada: avisa no topo. Onde o Praxis sabe se atualizar sozinho (Windows; Linux
// pelo .deb) o botão atualiza; nos outros, abre a página de versões.
const PAGINA_VERSOES = "https://github.com/disouz4-dev/praxis/releases/latest";
async function verificarAtualizacao() {
  let r;
  try { r = await invoke("verificar_atualizacao"); } catch { return; }
  if (!r || !r.nova) return;
  vivo("atualizacao_texto", () => tf("upd_available", { new: r.nova, cur: r.atual }));
  $("atualizacao").hidden = false;
  ligarAtualizar($("atualizar"), "atualizacao_texto", r);
}

function ligarAtualizar(botao, statusId, r) {
  botao.hidden = false;
  if (!r.pode_atualizar) {
    botao.onclick = () => invoke("abrir_link", { url: PAGINA_VERSOES });
    return;
  }
  botao.onclick = async () => {
    botao.disabled = true;
    vivo(statusId, () => t("upd_running"));
    try { await invoke("atualizar"); }
    catch (e) { fixo(statusId, String(e)); botao.disabled = false; }
  };
}

// Sobre: a versão instalada e "Verificar atualização" a qualquer momento.
function abrirSobre() {
  vivo("sobre_versao", () => tf("about_version", { v: ESTADO.versao }));
  fixo("sobre_status", ""); $("sobre_atualizar").hidden = true;
  $("sobre").showModal();
}

async function verificarNoSobre() {
  $("sobre_verificar").disabled = true; $("sobre_atualizar").hidden = true;
  vivo("sobre_status", () => t("upd_checking"));
  let r;
  try { r = await invoke("verificar_atualizacao"); } catch (e) { r = { erro: String(e) }; }
  $("sobre_verificar").disabled = false;
  if (r.erro) vivo("sobre_status", () => t("upd_error"));
  else if (r.nova) {
    vivo("sobre_status", () => tf("upd_available", { new: r.nova, cur: r.atual }) + (r.pode_atualizar ? "" : " " + t("upd_not_here")));
    ligarAtualizar($("sobre_atualizar"), "sobre_status", r);
  } else vivo("sobre_status", () => tf("upd_latest", { v: r.atual }));
}

function aplicarTemaInicial() {
  aplicarTema();
}

// sem o i18n.json carregado não há tradução: cai no português
main().catch((e) => { document.body.textContent = I18N ? tf("err_open", { err: e }) : "Erro ao abrir o Praxis: " + e; });
