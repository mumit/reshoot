// A repair picks a target; it never clicks the app or changes the expected result.
(() => {
  const host = document.createElement('reshoot-repair');
  host.style.cssText = 'position:fixed;bottom:16px;left:50%;transform:translateX(-50%);z-index:2147483647';
  const root = host.attachShadow({mode: 'open'});
  root.innerHTML = `<style>
    :host { color-scheme:light; font:14px/1.5 system-ui,sans-serif; color:#172033 }
    .panel { max-width:85vw; width:560px; background:white; padding:16px; border:1px solid #cbd5e1; border-radius:14px; box-shadow:0 8px 32px #0003 }
    p { margin:0 0 10px } button { font:inherit; border:1px solid #cbd5e1; border-radius:8px; padding:8px 12px; cursor:pointer }
    button:disabled { opacity:.4; cursor:default } #use { background:#2563eb; color:white } code { overflow-wrap:anywhere }
  </style><div class="panel" role="region" aria-label="Choose a replacement control">
    <p><strong>Choose the replacement control</strong><br>Click it to select it. Its action will not run.</p>
    <p id="choice" role="status">No control selected.</p><details><summary>Control details</summary><code id="selector"></code></details>
    <button id="use" disabled>Use this control</button> <button id="cancel">Cancel repair</button>
  </div>`;
  document.body.append(host);
  let selection = null, chosen = null, previous = '';
  const own = ev => ev.composedPath().includes(host);
  const stop = ev => { if (!own(ev)) { ev.preventDefault(); ev.stopImmediatePropagation(); } };
  for (const kind of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'dblclick', 'contextmenu']) addEventListener(kind, stop, true);
  addEventListener('click', ev => {
    if (own(ev)) return;
    stop(ev);
    const element = ev.target.closest('button,input,textarea,select,a,[role=button],[role=tab],[contenteditable=true]') || ev.target;
    if ([document.body, document.documentElement].includes(element)) return;
    const kind = window.__reshootRepairOperation;
    const valid = kind === 'type' ? element.isContentEditable || (!element.readOnly && (element.tagName === 'TEXTAREA' ||
      (element.tagName === 'INPUT' && !['button','submit','reset','checkbox','radio','file','hidden','range','color'].includes(element.type))))
      : kind === 'select' ? element.tagName === 'SELECT'
      : ['check','checked'].includes(kind) ? element.matches('input[type=checkbox],input[type=radio],[role=checkbox],[role=radio],[role=switch]')
      : kind === 'upload' ? element.matches('input[type=file]') : kind === 'value' ? 'value' in element : true;
    if (!valid || (['click','type','select','check','key','upload'].includes(kind) && element.disabled)) {
      if (chosen) chosen.style.outline = previous;
      chosen = null;
      root.getElementById('choice').textContent = 'Choose a control that can perform this ' + kind + ' step.';
      root.getElementById('use').disabled = true; selection = null; return;
    }
    if (chosen) chosen.style.outline = previous;
    chosen = element; previous = element.style.outline; element.style.outline = '3px solid #2563eb';
    const targets = window.__reshootTargets(element);
    const target = targets[0] || {css: window.__reshootPath(element)};
    selection = {target, fallbacks: targets.filter(value => JSON.stringify(value) !== JSON.stringify(target))};
    const label = element.getAttribute('aria-label') || element.getAttribute('placeholder') ||
      (element.labels && element.labels[0] ? element.labels[0].innerText : '') || element.innerText || element.tagName;
    root.getElementById('choice').textContent = 'Selected: ' + label.trim().replace(/\s+/g, ' ').slice(0,120);
    root.getElementById('selector').textContent = JSON.stringify(target);
    root.getElementById('use').disabled = false;
  }, true);
  root.getElementById('use').onclick = () => window.__reshootChoose(selection);
  root.getElementById('cancel').onclick = () => window.__reshootChoose(null);
  addEventListener('keydown', ev => {
    if (ev.key === 'Escape') { ev.preventDefault(); window.__reshootChoose(null); }
    else if (!own(ev)) { ev.preventDefault(); ev.stopImmediatePropagation(); }
  }, true);
})();
