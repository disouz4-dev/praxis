"use strict";
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const calmo = matchMedia("(prefers-reduced-motion: reduce)").matches;
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

/* ── navegação e barra de progresso ── */
const nav = $(".nav"), barra = $(".progresso");
function aoRolar() {
  const y = scrollY, max = document.documentElement.scrollHeight - innerHeight;
  nav.classList.toggle("solida", y > 20);
  barra.style.transform = `scaleX(${max > 0 ? y / max : 0})`;
}
addEventListener("scroll", aoRolar, { passive: true });
aoRolar();

/* ── aparecer ao rolar (em cascata dentro de cada seção) ── */
const observador = new IntersectionObserver((itens) => {
  for (const it of itens) {
    if (!it.isIntersecting) continue;
    const irmaos = $$(".revelar:not(.visivel)", it.target.parentElement);
    it.target.style.transitionDelay = `${Math.min(irmaos.indexOf(it.target), 4) * 90}ms`;
    it.target.classList.add("visivel");
    observador.unobserve(it.target);
  }
}, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });
$$(".revelar, .janela").forEach((el) => observador.observe(el));

/* ── brilho que segue o mouse nos cartões ── */
$$(".brilho").forEach((c) => c.addEventListener("pointermove", (e) => {
  const r = c.getBoundingClientRect();
  c.style.setProperty("--mx", `${e.clientX - r.left}px`);
  c.style.setProperty("--my", `${e.clientY - r.top}px`);
}));

/* ── abertura: legendas ao vivo (a tradução vem logo atrás da fala) ── */
const frases = [
  ["Bom dia a todos, obrigado por virem hoje.", "Good morning everyone, thank you for coming today."],
  ["Vamos apresentar o nosso projeto novo.", "Let's present our new project."],
  ["Pode me interromper se tiver alguma dúvida.", "Feel free to interrupt me if you have any questions."],
  ["A tradução acontece enquanto eu falo.", "The translation happens while I speak."],
];
const legFonte = $("#leg-fonte"), legDestino = $("#leg-destino");
let falando = 0, traduzindo = 0;   // intensidade das ondas (0–1)
const palavras = (el, txt) => {
  el.innerHTML = txt.split(" ").map((w) => `<span class="p">${w}</span> `).join("");
  return $$(".p", el);
};
async function legendas() {
  for (let i = 0; ; i = (i + 1) % frases.length) {
    const [fonte, destino] = frases[i];
    const pf = palavras(legFonte, fonte), pd = palavras(legDestino, destino);
    if (calmo) { pf.concat(pd).forEach((p) => p.classList.add("on")); await esperar(4000); continue; }
    const passo = 330, atraso = 3;   // a tradução começa depois de ~3 palavras confirmadas
    const total = Math.max(pf.length, pd.length + atraso);
    for (let k = 0; k < total + 1; k++) {
      falando = k < pf.length ? 1 : 0;
      traduzindo = k >= atraso && k - atraso < pd.length ? 1 : 0;
      if (pf[k]) pf[k].classList.add("on");
      const j = k - atraso;
      if (j >= 0 && pd[j]) pd[j].classList.add("on");
      await esperar(passo);
    }
    falando = traduzindo = 0;
    await esperar(1600);
    legFonte.style.opacity = legDestino.style.opacity = 0;
    await esperar(350);
    legFonte.style.opacity = legDestino.style.opacity = 1;
  }
}
legFonte.style.transition = legDestino.style.transition = "opacity .35s";
legendas();

/* ── abertura: ondas (azul = sua voz, violeta = a tradução) ── */
const cv = $("#ondas"), cx = cv.getContext("2d");
let aF = 0, aT = 0;
function desenharOndas(t) {
  const dpr = Math.min(devicePixelRatio || 1, 2), w = cv.clientWidth, h = cv.clientHeight;
  if (cv.width !== w * dpr || cv.height !== h * dpr) { cv.width = w * dpr; cv.height = h * dpr; }
  cx.setTransform(dpr, 0, 0, dpr, 0, 0);
  cx.clearRect(0, 0, w, h);
  aF += ((falando ? 1 : 0.12) - aF) * 0.06;
  aT += ((traduzindo ? 1 : 0.12) - aT) * 0.06;
  const s = t / 1000;
  for (let n = 0; n < 4; n++) {
    const g = cx.createLinearGradient(0, 0, w, 0);
    g.addColorStop(0, `rgba(79,140,255,${0.9 - n * 0.18})`);
    g.addColorStop(0.5, `rgba(167,139,250,${0.85 - n * 0.18})`);
    g.addColorStop(1, `rgba(34,211,238,${0.8 - n * 0.18})`);
    cx.strokeStyle = g;
    cx.lineWidth = n === 0 ? 2.2 : 1.2;
    cx.beginPath();
    for (let x = 0; x <= w; x += 3) {
      const u = x / w;
      const amp = (aF * (1 - u) + aT * u) * (h * 0.36) * Math.sin(Math.PI * u) ** 0.8;
      const y = h / 2 + amp * (Math.sin(u * 14 + s * (3.2 + n * 0.7) + n) * 0.6 +
                               Math.sin(u * 31 - s * (5.1 + n) + n * 2) * 0.3 +
                               Math.sin(u * 7 + s * 1.3) * 0.25) * (1 - n * 0.18);
      x ? cx.lineTo(x, y) : cx.moveTo(x, y);
    }
    cx.stroke();
  }
  if (!calmo) requestAnimationFrame(desenharOndas);
}
requestAnimationFrame(desenharOndas);

/* ── linha do tempo: fala original × tradução falada ── */
const lt = {
  fonte: [["Bom dia a todos,", 0, 24], ["obrigado por virem", 25, 50], ["hoje à reunião.", 51, 72]],
  destino: [["Good morning everyone,", 18, 44], ["thank you for coming", 45, 70], ["to the meeting today.", 71, 92]],
};
const ltF = $("#lt-fonte"), ltD = $("#lt-destino"), agulha = $("#lt-agulha");
const blocos = (el, itens) => itens.map(([txt, a, b]) => {
  const d = document.createElement("div");
  d.className = "bloco"; d.textContent = txt;
  d.style.left = `${a}%`; d.style.width = `${b - a}%`;
  d.style.transitionDuration = `${(b - a) * 45}ms`;
  el.appendChild(d);
  return { d, a };
});
const bF = blocos(ltF, lt.fonte), bD = blocos(ltD, lt.destino);
let ltRodando = false;
async function linhaDoTempo() {
  if (ltRodando) return;
  ltRodando = true;
  for (;;) {
    [...bF, ...bD].forEach((b) => b.d.classList.remove("on"));
    for (let p = 0; p <= 100; p += 0.5) {
      const r = ltF.getBoundingClientRect(), c = $("#linha-tempo").getBoundingClientRect();
      agulha.style.left = `${r.left - c.left + (r.width * p) / 100}px`;
      for (const b of [...bF, ...bD]) if (p >= b.a) b.d.classList.add("on");
      await esperar(calmo ? 0 : 22);
    }
    await esperar(2200);
  }
}
new IntersectionObserver((it, o) => { if (it[0].isIntersecting) { linhaDoTempo(); o.disconnect(); } }, { threshold: 0.3 })
  .observe($("#linha-tempo"));

/* ── voz: barras que "falam" ── */
const barrasVoz = $("#barras-voz");
const nBarras = 28;
for (let i = 0; i < nBarras; i++) barrasVoz.appendChild(document.createElement("i"));
const bv = $$("i", barrasVoz);
let fase = 0;
setInterval(() => {
  fase += 0.35;
  const env = 0.55 + 0.45 * Math.sin(fase * 0.4);
  bv.forEach((b, i) => {
    const c = 1 - Math.abs(i - nBarras / 2) / (nBarras / 2);
    const v = (0.25 + 0.75 * Math.abs(Math.sin(fase + i * 0.55) * Math.cos(fase * 0.7 + i * 0.23))) * env * (0.35 + 0.65 * c);
    b.style.height = `${Math.max(8, v * 100)}%`;
  });
}, calmo ? 100000 : 120);

/* ── aplicativo: começa a demonstração quando aparece na tela ── */
const demo = $("#demo-app");
new IntersectionObserver((it) => {
  if (it[0].isIntersecting) setTimeout(() => demo.contentWindow?.postMessage("iniciar", "*"), 900);
}, { threshold: 0.5 }).observe(demo);

/* ── player da conversa ── */
const audio = $("#audio"), botao = $("#tocar"), onda = $("#onda-player"), tempo = $("#tempo");
const N = innerWidth < 640 ? 42 : 72;
for (let i = 0; i < N; i++) {
  const b = document.createElement("i");
  b.style.height = `${18 + 60 * Math.abs(Math.sin(i * 1.7) * Math.cos(i * 0.37))}%`;
  onda.appendChild(b);
}
const barrasP = $$("i", onda);
const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
// o desenho segue o volume real do áudio, quando o navegador consegue ler o arquivo
fetch(audio.currentSrc || audio.src).then((r) => r.arrayBuffer())
  .then((buf) => new (window.AudioContext || window.webkitAudioContext)().decodeAudioData(buf))
  .then((dados) => {
    const ch = dados.getChannelData(0), pedaco = Math.floor(ch.length / N);
    const picos = barrasP.map((_, i) => {
      let m = 0;
      for (let k = i * pedaco; k < (i + 1) * pedaco; k += 64) m = Math.max(m, Math.abs(ch[k]));
      return m;
    });
    const maior = Math.max(...picos) || 1;
    barrasP.forEach((b, i) => { b.style.height = `${Math.max(8, (picos[i] / maior) * 100)}%`; });
  }).catch(() => {});
botao.onclick = () => (audio.paused ? audio.play() : audio.pause());
audio.onplay = () => botao.classList.add("tocando");
audio.onpause = audio.onended = () => botao.classList.remove("tocando");
audio.ontimeupdate = () => {
  const p = audio.duration ? audio.currentTime / audio.duration : 0;
  barrasP.forEach((b, i) => b.classList.toggle("passou", i / N < p));
  tempo.textContent = mmss(audio.currentTime);
};
audio.onloadedmetadata = () => { tempo.textContent = mmss(audio.duration); };
onda.onclick = (e) => {
  const r = onda.getBoundingClientRect();
  if (audio.duration) audio.currentTime = ((e.clientX - r.left) / r.width) * audio.duration;
  if (audio.paused) audio.play();
};

/* ── números contando ── */
const contador = new IntersectionObserver((itens) => {
  for (const it of itens) {
    if (!it.isIntersecting) continue;
    const el = it.target, ate = +el.dataset.ate, pre = el.dataset.pre || "", suf = el.dataset.suf || "";
    const t0 = performance.now(), dur = calmo ? 0 : 1400;
    const passo = (t) => {
      const p = dur ? Math.min(1, (t - t0) / dur) : 1;
      el.textContent = pre + Math.round(ate * (1 - (1 - p) ** 3)) + suf;
      if (p < 1) requestAnimationFrame(passo);
    };
    requestAnimationFrame(passo);
    contador.unobserve(el);
  }
}, { threshold: 0.6 });
$$(".valor").forEach((v) => contador.observe(v));

/* ── copiar comandos ── */
$$(".copiar").forEach((b) => b.onclick = async () => {
  const txt = $("code", b.parentElement).textContent;
  try { await navigator.clipboard.writeText(txt); } catch {
    const r = document.createRange(); r.selectNodeContents($("code", b.parentElement));
    getSelection().removeAllRanges(); getSelection().addRange(r); document.execCommand("copy");
  }
  b.textContent = "Copiado ✓"; b.classList.add("ok");
  setTimeout(() => { b.textContent = "Copiar"; b.classList.remove("ok"); }, 1800);
});
