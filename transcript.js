// 스크립트 페이지: 언어 전환 + 본문 찾기
const T = {
  ko: {back: "← 튜터로", sub: "원문 영어 자막이에요 · 타임스탬프를 누르면 그 장면부터 재생돼요", yt: "YouTube에서 보기", find: "스크립트에서 찾기"},
  en: {back: "← Back to tutor", sub: "Original English captions · Click a timestamp to jump to that moment", yt: "Watch on YouTube", find: "Search the transcript"},
};
const store = {get: k => { try { return localStorage.getItem(k) } catch { return null } }, set: (k, v) => { try { localStorage.setItem(k, v) } catch {} }};
const seg = document.querySelector(".seg");
function setLang(l) {
  document.documentElement.lang = l; store.set("lang", l);
  document.querySelectorAll("[data-i18n]").forEach(e => e.textContent = T[l][e.dataset.i18n]);
  document.querySelectorAll("[data-i18n-ph]").forEach(e => e.placeholder = T[l][e.dataset.i18nPh]);
  document.querySelectorAll("[data-ko]").forEach(e => e.textContent = e.dataset[l]);
  seg.querySelectorAll("button").forEach(b => {
    const on = b.dataset.lang === l; b.setAttribute("aria-pressed", on);
    if (on) { seg.style.setProperty("--x", b.offsetLeft + "px"); seg.style.setProperty("--w", b.offsetWidth + "px") }
  });
}
seg.onclick = e => e.target.dataset.lang && setLang(e.target.dataset.lang);
setLang(store.get("lang") || (navigator.language.startsWith("ko") ? "ko" : "en"));

// 찾기: 일치하는 문단만 남기고 단어를 강조
const paras = [...document.querySelectorAll("#tx p")].map(p => [p, p.innerHTML]);
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
let timer;
document.getElementById("q").oninput = e => {
  clearTimeout(timer);
  timer = setTimeout(() => {
    const q = e.target.value.trim(), re = q && new RegExp(`(${esc(q)})`, "gi");
    for (const [p, h] of paras) {
      if (!q) { p.innerHTML = h; p.hidden = false; continue }
      const a = p.firstElementChild.outerHTML, text = p.textContent.slice(p.firstElementChild.textContent.length);
      const hit = re.test(text); re.lastIndex = 0;
      p.hidden = !hit;
      if (hit) p.innerHTML = a + text.replace(/[&<>]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;"})[c]).replace(re, "<mark>$1</mark>");
    }
  }, 150);
};
