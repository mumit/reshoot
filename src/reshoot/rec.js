// Added by `reshoot rec` to every page it opens: it watches what a person does (clicks, typing, Enter, scrolling)
// and reports each action with a selector that should still find the element in the next take.
(() => {
  if (window.__reshootRecording) return;
  window.__reshootRecording = true;
  const send = ev => { try { window.__reshootRec(JSON.stringify(ev)); } catch {} };
  const css = s => (window.CSS && CSS.escape ? CSS.escape(s) : s.replace(/[^\w-]/g, "\\$&"));
  const unique = sel => { try { return document.querySelectorAll(sel).length === 1; } catch { return false; } };
  // ids and classes made by a framework or a build change between versions: "css-1x2y3z", "r:12:", "ember123"
  const madeUp = s => /\d{3,}|^[a-z]+-[a-z0-9]{5,}$|^:r|^r:|[A-Z0-9]{6,}/.test(s);

  // The most stable way to find e again: a test id, an id, a name, a label, its text, then its place in the page.
  // Returns [kind, value]: "css" for a selector, "text" for a [tag, text] pair found by its words.
  function locate(e) {
    for (const attr of ["data-testid", "data-test", "data-cy", "data-qa"]) {
      const v = e.getAttribute(attr);
      if (v && unique(`[${attr}="${css(v)}"]`)) return ["css", `[${attr}="${css(v)}"]`];
    }
    if (e.id && !madeUp(e.id) && unique("#" + css(e.id))) return ["css", "#" + css(e.id)];
    const tag = e.tagName.toLowerCase();
    for (const attr of ["name", "aria-label", "placeholder", "title"]) {
      const v = e.getAttribute(attr);
      if (v && unique(`${tag}[${attr}="${css(v)}"]`)) return ["css", `${tag}[${attr}="${css(v)}"]`];
    }
    const text = (e.innerText || e.value || "").trim().replace(/\s+/g, " ");
    if (["a", "button", "summary", "label"].includes(tag) || e.getAttribute("role") === "button" || e.getAttribute("role") === "tab") {
      if (text && text.length <= 40) {
        const same = [...document.querySelectorAll(tag)].filter(x => (x.innerText || "").trim().replace(/\s+/g, " ") === text);
        if (same.length === 1) return ["text", [tag, text]];
      }
    }
    return ["css", path(e) || tag];
  }

  // A path from the nearest ancestor with a stable id (or the body), with :nth-of-type where it's needed. It always
  // goes up to that anchor: "li" may be the only list item now, but "#list > li" still means the same one later.
  function path(e) {
    const parts = [];
    for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
      if (n === document.body) { parts.unshift("body"); break; }
      if (n.id && !madeUp(n.id) && unique("#" + css(n.id))) { parts.unshift("#" + css(n.id)); break; }
      let part = n.tagName.toLowerCase();
      const sibs = n.parentElement ? [...n.parentElement.children].filter(x => x.tagName === n.tagName) : [];
      if (sibs.length > 1) part += `:nth-of-type(${sibs.indexOf(n) + 1})`;
      parts.unshift(part);
    }
    return parts.join(" > ");
  }

  // Clicks on what's really clickable, not the span inside the button.
  const target = e => e.closest("a, button, input, textarea, select, label, summary, [role=button], [role=tab], [onclick], [contenteditable=true]") || e;
  const field = e => e && (e.matches("input:not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit]), textarea") || e.isContentEditable);

  // A click with no mouse behind it (detail 0) is the browser's own: Enter in a form "clicks" its submit button.
  // Recording it too would submit twice on replay, since the Enter is recorded already.
  // A click on the page's background (the body itself) does nothing, so it isn't recorded.
  addEventListener("click", ev => {
    if (!ev.isTrusted || ev.detail === 0) return;
    const e = target(ev.target);
    if (e === document.body || e === document.documentElement || !e.tagName) return;
    send({ kind: "click", where: locate(e), field: !!field(e) });
  }, true);
  // What a field held before the typing started, so replaying can tell adding text from clearing or changing it.
  const valueOf = e => (e.isContentEditable ? e.innerText : e.value) || "";
  const before = new WeakMap();
  addEventListener("focusin", ev => { if (field(ev.target)) before.set(ev.target, valueOf(ev.target)); }, true);
  addEventListener("input", ev => {
    if (!ev.isTrusted || !field(ev.target)) return;
    const e = ev.target;
    send({ kind: "type", where: locate(e), value: valueOf(e), before: before.get(e) ?? "", secret: e.type === "password" });
  }, true);
  addEventListener("keydown", ev => {
    if (!ev.isTrusted || !["Enter", "Escape", "Tab"].includes(ev.key)) return;
    send({ kind: "key", key: ev.key, where: locate(ev.target) });
  }, true);
  let scrolled = 0, settle;
  addEventListener("scroll", () => {
    const y = document.scrollingElement.scrollTop;
    clearTimeout(settle);
    settle = setTimeout(() => { if (Math.abs(y - scrolled) > 40) send({ kind: "scroll", dy: Math.round(y - scrolled) }); scrolled = y; }, 300);
  }, { passive: true });
  addEventListener("DOMContentLoaded", () => { scrolled = document.scrollingElement ? document.scrollingElement.scrollTop : 0; });
})();
