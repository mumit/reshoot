// Added by `reshoot web` to the page it records, never part of the app: a cursor that glides to things and clicks
// them, typing that looks like a person's, and captions. Everything is drawn above the page and ignores the mouse.
// It's added to every document the tab loads, so it survives full page loads as well as #hash changes.
window.__demo = window.__demo || (() => {
  const style = document.createElement("style");
  style.textContent = `
    #__cur { position:fixed; z-index:2147483647; left:0; top:0; pointer-events:none; will-change:transform; }
    #__cur svg { display:block; filter:drop-shadow(0 2px 4px rgba(0,0,0,.45)); transition:transform .12s; }
    #__cur.down svg { transform:scale(.86); }
    .__ripple { position:fixed; z-index:2147483646; width:44px; height:44px; margin:-22px 0 0 -22px; border-radius:50%;
                border:2.5px solid rgba(255,255,255,.95); box-shadow:0 0 0 2px rgba(0,0,0,.15); pointer-events:none;
                animation:__ripple .55s cubic-bezier(.2,.7,.3,1) forwards; }
    @keyframes __ripple { from { transform:scale(.25); opacity:1 } to { transform:scale(1.5); opacity:0 } }
    #__cap { position:fixed; z-index:2147483645; left:50%; bottom:6.5%; transform:translate(-50%, 12px); opacity:0;
             max-width:min(80vw, 980px); padding:14px 26px; border-radius:16px; text-align:center; pointer-events:none;
             font:600 clamp(18px, 2.3vw, 30px)/1.25 -apple-system, BlinkMacSystemFont, system-ui, sans-serif; letter-spacing:-.01em;
             color:#fff; background:rgba(14,13,12,.78); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
             box-shadow:0 12px 40px rgba(0,0,0,.35); transition:opacity .35s, transform .35s; }
    #__cap.on { opacity:1; transform:translate(-50%, 0); }
    #__cap small { display:block; margin-top:4px; font-weight:500; font-size:.6em; color:rgba(255,255,255,.75); }`;
  const cur = document.createElement("div");
  cur.id = "__cur";
  cur.innerHTML = `<svg width="26" height="30" viewBox="0 0 26 30"><path d="M3 2 L3 24 L9 18.5 L13.2 27.5 L17.4 25.6 L13.3 16.8 L21.5 16.6 Z"
    fill="#111" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>`;
  const cap = document.createElement("div");
  cap.id = "__cap";
  const ready = () => {
    if (!style.isConnected && document.head) document.head.append(style);
    if (document.body && !cur.isConnected) document.body.append(cur, cap);
  };
  ready(); addEventListener("DOMContentLoaded", ready);

  // The cursor starts where it was on the last page, so it doesn't jump when a link opens a new one.
  let x = innerWidth * 0.62, y = innerHeight * 0.72;
  try { [x, y] = JSON.parse(sessionStorage.__demoXY) ?? [x, y]; } catch {}
  const place = () => { cur.style.transform = `translate(${x - 3}px, ${y - 2}px)`; };
  addEventListener("pagehide", () => { try { sessionStorage.__demoXY = JSON.stringify([x, y]); } catch {} });
  place();
  const sleep = ms => new Promise(ok => setTimeout(ok, ms));
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  // The tag (such as "button") whose words are text, for things best found by what they say.
  const byText = (tag, text) => {
    const norm = s => (s || "").trim().replace(/\s+/g, " ");
    const e = [...document.querySelectorAll(tag)].find(x => norm(x.innerText || x.value) === text);
    if (!e) throw new Error(`no ${tag} says "${text}"`);
    return e;
  };
  const el = sel => {
    const e = typeof sel === "string" ? document.querySelector(sel) : sel;
    if (!e) throw new Error("nothing matches " + sel);
    return e;
  };

  // Waits until something matches, for results that take a moment. A fixed hold is too short on a slow run.
  async function waitFor(sel, ms = 10000) {
    const t0 = performance.now();
    while (performance.now() - t0 < ms) {
      const e = typeof sel === "function" ? sel() : document.querySelector(sel);
      if (e) return e;
      await sleep(50);
    }
    throw new Error("still nothing matches " + sel + " after " + ms + " ms");
  }

  // Glides along a slight curve, as a hand does, taking longer for longer trips.
  async function moveTo(tx, ty, ms) {
    ready();
    const sx = x, sy = y, d = Math.hypot(tx - sx, ty - sy);
    ms = ms ?? Math.min(1100, 380 + d * 0.6);
    const bend = (Math.random() - .5) * Math.min(120, d * .25), nx = -(ty - sy) / (d || 1), ny = (tx - sx) / (d || 1);
    const t0 = performance.now();
    await new Promise(done => {
      const step = now => {
        const t = Math.min(1, (now - t0) / ms), e = ease(t), arc = Math.sin(Math.PI * e) * bend;
        x = sx + (tx - sx) * e + nx * arc; y = sy + (ty - sy) * e + ny * arc; place();
        t < 1 ? requestAnimationFrame(step) : done();
      };
      requestAnimationFrame(step);
    });
  }

  // Tells reshoot what happened and where, for zooming afterwards and for captions drawn after the zoom.
  // reshoot adds window.__reshoot while recording; without it (a page opened by hand) this does nothing.
  function report(ev) {
    try { window.__reshoot && window.__reshoot(JSON.stringify(ev)); } catch {}
  }
  const box = e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; };

  // An action (moving to, clicking, typing) is reported once, with where its element is, when it starts and ends.
  let acting = 0;
  async function act(e, run) {
    if (!acting) report({ kind: "act", phase: "start", rect: box(e) });
    acting++;
    try { return await run(); }
    finally { if (!--acting) report({ kind: "act", phase: "end", rect: box(e) }); }
  }

  async function to(sel, { dx = 0.5, dy = 0.5, ms } = {}) {
    const e = el(sel);
    e.scrollIntoView({ block: "nearest", inline: "nearest" });
    return act(e, async () => {
      const r = e.getBoundingClientRect();
      await moveTo(r.left + r.width * dx, r.top + r.height * dy, ms);
      return e;
    });
  }

  // Zooms in on sel until zoomOut(), whatever the automatic zoom would do. scale is how much to enlarge.
  function zoom(sel, { scale } = {}) {
    const e = el(sel);
    e.scrollIntoView({ block: "nearest", inline: "nearest" });
    report({ kind: "zoom", rect: box(e), scale: scale ?? null });
  }
  const zoomOut = () => report({ kind: "zoom-out" });

  // The events a real click sends, in order. e.click() alone skips pointerdown and mousedown, which many apps use.
  function press(e) {
    const at = { bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y, button: 0 };
    e.dispatchEvent(new PointerEvent("pointerdown", { ...at, pointerType: "mouse", isPrimary: true }));
    e.dispatchEvent(new MouseEvent("mousedown", at));
    if (e.focus) e.focus({ preventScroll: true });
    e.dispatchEvent(new PointerEvent("pointerup", { ...at, pointerType: "mouse", isPrimary: true }));
    e.dispatchEvent(new MouseEvent("mouseup", at));
    e.click();
  }

  async function click(sel, opts) {
    const e = el(sel);
    e.scrollIntoView({ block: "nearest", inline: "nearest" });
    return act(e, () => clickNow(e, opts));
  }

  async function clickNow(e, opts) {
    await to(e, opts);
    await sleep(90);
    cur.classList.add("down");
    const ring = document.createElement("div");
    ring.className = "__ripple"; ring.style.left = x + "px"; ring.style.top = y + "px";
    document.body.append(ring); setTimeout(() => ring.remove(), 700);
    await sleep(110);
    cur.classList.remove("down");
    press(e);
    return e;
  }

  // Sets a field's value through the browser's own setter, so React and other frameworks see the change.
  function setValue(e, v) {
    const proto = e instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, "value").set.call(e, v);
  }

  // Types like a person: an uneven rhythm, a little longer after a space.
  async function type(sel, text, opts) {
    const e = el(sel);
    e.scrollIntoView({ block: "nearest", inline: "nearest" });
    return act(e, () => typeNow(e, text, opts));
  }

  async function typeNow(e, text, { cps = 13, clear = false } = {}) {
    await click(e);
    e.focus();
    if (clear && !e.isContentEditable) { setValue(e, ""); e.dispatchEvent(new Event("input", { bubbles: true })); }
    for (const ch of text) {
      if (e.isContentEditable) document.execCommand("insertText", false, ch);
      else { setValue(e, e.value + ch); e.dispatchEvent(new InputEvent("input", { bubbles: true, data: ch, inputType: "insertText" })); }
      await sleep(1000 / cps * (0.55 + Math.random() * 0.9) + (ch === " " ? 70 : 0));
    }
    e.dispatchEvent(new Event("change", { bubbles: true }));
    return e;
  }

  // Presses a key in the focused element (or sel), such as "Enter" or "Escape". A made-up Enter doesn't submit a
  // form the way a real one does, so the form is submitted here, unless the page handled the key itself.
  function key(name, sel) {
    const e = sel ? el(sel) : document.activeElement || document.body;
    let handled = false;
    for (const t of ["keydown", "keypress", "keyup"])
      handled = !e.dispatchEvent(new KeyboardEvent(t, { key: name, code: name, bubbles: true, cancelable: true })) || handled;
    if (name === "Enter" && e.form && !handled) e.form.requestSubmit();
    return e;
  }

  // Scrolls the page (or sel's box) by dy pixels, smoothly, and waits until it's done.
  async function scroll(dy, { sel, ms = 900 } = {}) {
    const box = sel ? el(sel) : document.scrollingElement, from = box.scrollTop, t0 = performance.now();
    await new Promise(done => {
      const step = now => {
        const t = Math.min(1, (now - t0) / ms);
        box.scrollTop = from + dy * ease(t);
        t < 1 ? requestAnimationFrame(step) : done();
      };
      requestAnimationFrame(step);
    });
  }

  // With zoom on, reshoot draws captions after zooming, so they stay put; the page only reports them.
  function caption(text, sub) {
    ready();
    report({ kind: "caption", text: text || null, sub: sub || null });
    if (window.__reshootPostCaptions) return;
    if (!text) return cap.classList.remove("on");
    cap.innerHTML = text + (sub ? `<small>${sub}</small>` : "");
    cap.classList.add("on");
  }

  // Blurs everything matching sel, now and whatever the page adds later, until unblur(sel): for an avatar, an
  // account name, an email in a header. It's a style rule, so it survives the page redrawing the element.
  // The storyboard's BLUR list is blurred on every page from the start.
  const blurred = new Map(), blurStyle = document.createElement("style");
  function blurRules() {
    blurStyle.textContent = [...blurred].map(([sel, px]) => `${sel} { filter: blur(${px}px) !important; }`).join("\n");
    const into = document.head || document.documentElement;  // neither exists yet as a new page starts
    if (into && !blurStyle.isConnected) into.append(blurStyle);
  }
  function blur(sel, { px = 12 } = {}) {
    document.querySelectorAll(sel);  // a bad selector fails here, in the beat, not silently
    blurred.set(sel, px); blurRules();
  }
  function unblur(sel) { blurred.delete(sel); blurRules(); }
  for (const sel of window.__reshootBlur || []) blurred.set(sel, 12);
  if (blurred.size) { blurRules(); addEventListener("DOMContentLoaded", blurRules); }

  const hide = () => { cur.style.opacity = 0; };
  const show = () => { cur.style.opacity = 1; };
  return { moveTo, to, click, type, key, scroll, waitFor, caption, sleep, hide, show, zoom, zoomOut, byText, blur, unblur };
})();
