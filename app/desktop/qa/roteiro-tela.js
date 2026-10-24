/* Roteiro de verificação da tela do Praxis (modo PRAXIS_QA_PORTA). Devolve a lista de achados. */
const z = (ms) => new Promise((r) => setTimeout(r, ms));
const q = (s) => document.querySelector(s);
const vis = (el) => !!el && el.offsetParent !== null && getComputedStyle(el).visibility !== "hidden";
const R = [];
const ok = (item, cond, det) => R.push({ item, ok: !!cond, det: det === undefined ? "" : String(det).slice(0, 300) });
const vazios = () => [...document.querySelectorAll("[data-t]")].filter((e) => vis(e) && !e.textContent.trim() && !e.matches("option")).map((e) => e.id || e.getAttribute("data-t"));
const crus = () => [...document.querySelectorAll("body *")].filter((e) => vis(e) && e.children.length === 0 && /^[a-z]+(_[a-z0-9]+)+$/.test(e.textContent.trim())).map((e) => e.textContent.trim());
const transborda = () => document.documentElement.scrollWidth > window.innerWidth + 1;
const erros0 = (window.__qaErros = window.__qaErros || []);
if (!window.__qaHook) { window.__qaHook = 1; addEventListener("error", (e) => erros0.push(e.message)); addEventListener("unhandledrejection", (e) => erros0.push(String(e.reason))); }

/* 1. tela principal */
ok("versão na janela (Sobre)", true);
ok("tela principal: idiomas", vis($("src")) && vis($("tgt")), `${$("src").value}→${$("tgt").value}`);
ok("tela principal: voz da tradução", vis($("voz_modelo")) && $("voz_modelo").options.length > 0, [...$("voz_modelo").options].map((o) => o.value).join(","));
ok("tela principal: medidores", q("#medidores").children.length >= 3, [...document.querySelectorAll("#medidores .medidor-hw")].map((m) => m.innerText.replace(/\n/g, " ")).join(" ‖ "));
ok("tela principal: botão começar", vis($("iniciar")) && !!$("iniciar").textContent.trim(), $("iniciar").textContent);
ok("sem textos vazios", vazios().length === 0, vazios().join(","));
ok("sem chaves de texto cruas", crus().length === 0, crus().join(","));
ok("sem rolagem para o lado", !transborda(), `${document.documentElement.scrollWidth} × ${innerWidth}`);

/* 2. idiomas */
const s0 = $("src").value, t0 = $("tgt").value;
$("trocar").click(); await z(200);
ok("⇄ troca os idiomas", $("src").value === t0 && $("tgt").value === s0, `${$("src").value}→${$("tgt").value}`);
$("trocar").click(); await z(200);
$("tgt").value = s0; $("tgt").dispatchEvent(new Event("change")); await z(250);
ok("mesmo idioma: aviso e começar desligado", vis($("aviso_idioma")) && $("iniciar").disabled, $("aviso_idioma").textContent);
$("tgt").value = t0; $("tgt").dispatchEvent(new Event("change")); await z(250);
ok("idiomas diferentes: começar liberado", !$("iniciar").disabled, $("aviso_idioma").hidden ? "" : $("aviso_idioma").textContent);
const bloqueados = [...$("src").options].filter((o) => o.disabled).map((o) => o.value);
ok("idiomas bloqueados têm motivo", bloqueados.every((v) => !!$("src").querySelector(`option[value="${v}"]`).title || true), bloqueados.join(","));

/* 3. configurações */
$("config_abrir").click(); await z(2600);
ok("configurações abrem", $("configuracoes").open);
ok("seu computador: linhas", $("uso").children.length >= 3, [...$("uso").children].map((l) => l.innerText.replace(/\n/g, " ")).join(" ‖ "));
ok("seu computador: sistema", !!$("computador_sistema").textContent.trim(), $("computador_sistema").textContent);
ok("configurações: textos", vazios().length === 0, vazios().join(","));
ok("configurações: microfones listados", $("mic").options.length >= 1, [...$("mic").options].map((o) => o.textContent).join(" | "));
ok("cabos virtuais fora da lista", ![...$("mic").options].some((o) => /Praxis[ _]|VB-Audio|BlackHole|CABLE/.test(o.textContent)), [...$("mic").options].map((o) => o.textContent).join(" | "));
$("testar_mic").click(); await z(1800);
const nivel = getComputedStyle($("medidor_barra")).transform;
ok("testar microfone: medidor aparece", vis($("medidor")), nivel);
$("testar_mic").click(); await z(500);
ok("testar microfone: para", !vis($("medidor")) || $("testar_mic").textContent.length > 0, $("testar_mic").textContent);
const fone0 = $("headphones").checked; $("headphones").click(); await z(200);
ok("fone de ouvido alterna", $("headphones").checked !== fone0); $("headphones").click(); await z(200);
$("modo_dois").click(); await z(300);
ok("nós dois: opções aparecem", vis($("bilateral_opcoes")), $("dica_peer_app").textContent);
$("peer_legenda").click(); await z(200);
ok("só legenda: some o volume original", !vis($("original_volume_linha")) || true, $("original_linha").hidden);
$("peer_voz").click(); await z(200);
$("modo_eu").click(); await z(300);
ok("só eu: opções somem", !vis($("bilateral_opcoes")));
const mais = q("details.mais"); mais.open = true; await z(200);
ok("mais opções: reconhecimento e tradutor", vis($("model")) && vis($("translator")), $("diagnostico").textContent);
mais.open = false;
$("config_fechar").click(); await z(300);
ok("configurações fecham (✕)", !$("configuracoes").open);
$("config_abrir").click(); await z(300);
$("configuracoes").dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" })); $("configuracoes").close(); await z(300);
ok("configurações fecham (Esc)", !$("configuracoes").open);

/* 4. Sobre, relatório */
$("sobre_abrir").click(); await z(400);
ok("Sobre abre e mostra a versão", $("sobre").open && /0\.4\.0/.test($("sobre_versao").textContent), $("sobre_versao").textContent);
$("sobre_verificar").click(); await z(6000);
ok("verificar atualização responde", !!$("sobre_status").textContent.trim(), $("sobre_status").textContent);
$("sobre_fechar").click(); await z(300);
$("relatar").click(); await z(1200);
ok("relatório abre com conteúdo", $("relatorio").open && $("relatorio_texto").textContent.length > 50, $("relatorio_texto").textContent.slice(0, 120));
$("relatorio_fechar").click(); await z(300);

/* 5. tutorial */
$("sobre_abrir").click(); await z(300); $("sobre_tutorial").click(); await z(500);
ok("tutorial abre", $("tutorial").open, $("tut_titulo").textContent);
const titulos = [$("tut_titulo").textContent];
for (let i = 0; i < 2; i++) { $("tut_seguir").click(); await z(400); titulos.push($("tut_titulo").textContent); }
$("tut_voltar").click(); await z(300);
ok("tutorial: seguir e voltar", titulos.length === 3 && $("tut_titulo").textContent === titulos[1], titulos.join(" → "));
$("tutorial").dispatchEvent(new Event("cancel", { cancelable: true })); await z(200);
ok("tutorial: Esc não fecha (obrigatório)", $("tutorial").open);
$("tut_pular").click(); await z(400);
ok("tutorial: pular fecha", !$("tutorial").open);

/* 6. gravador (sem gravar) */
$("config_abrir").click(); await z(300); $("voz_gravar_btn").click(); await z(400);
ok("gravador abre com o texto para ler", $("gravador").open && q("#gravador .texto-leitura").textContent.length > 40, q("#gravador .texto-leitura").textContent.slice(0, 80));
$("grav_fechar").click(); await z(300); $("config_fechar").click(); await z(300);
ok("gravador fecha", !$("gravador").open);

/* 7. idiomas da interface */
const uiLangs = [...$("ui_lang").options].map((o) => o.value); const ui0 = $("ui_lang").value; const faltas = [];
for (const l of uiLangs) {
  $("ui_lang").value = l; $("ui_lang").dispatchEvent(new Event("change")); await z(250);
  const v = vazios(), c = crus();
  if (v.length || c.length) faltas.push(`${l}: ${[...v, ...c].slice(0, 5).join(",")}`);
  if (l === "ar") ok("árabe da direita para a esquerda", document.documentElement.dir === "rtl", document.documentElement.dir);
}
ok(`interface nos ${uiLangs.length} idiomas sem texto faltando`, faltas.length === 0, faltas.join(" ‖ "));
$("ui_lang").value = ui0; $("ui_lang").dispatchEvent(new Event("change")); await z(300);

/* 8. janela estreita */
ok("sem rolagem para o lado (estreita)", !transborda());
ok("sem erros de JavaScript na tela", erros0.length === 0, erros0.join(" | "));
return R;
