/* Draft layout feedback stays separate from the pinned video and review. */
(() => {
  const output = document.getElementById('still-export'), image = document.getElementById('still-image');
  if (!output || !image) return;
  const status = document.getElementById('still-status'), toggle = document.getElementById('toggle-still');
  const video = document.getElementById('video');
  let generation = 0, timer, controller, url, wantStill = false, ready = false;
  document.body.dataset.stillReady = '1';
  const view = () => {
    image.hidden = !wantStill || !ready;
    if (!image.hidden) { document.body.dataset.layoutStill = '1'; video.pause(); }
    else delete document.body.dataset.layoutStill;
    toggle.textContent = wantStill && ready ? 'Show recorded video' : 'Show layout still';
    toggle.disabled = !ready;
  };
  const draft = () => {
    const panel = document.querySelector('.beat.selected');
    if (!panel) throw new Error('Choose a step to preview.');
    const look = document.querySelector('.look'), cut = document.querySelector('.cut');
    const result = {caption:panel.querySelector('[name=caption]').value, sub:panel.querySelector('[name=sub]').value};
    if (look) result.look = {position:look.querySelector('[name=position]').value,
      background:look.querySelector('[name=background]').value || '#0e0d0cc8',
      foreground:look.querySelector('[name=foreground]').value || '#ffffff'};
    if (cut) {
      const top = cut.querySelector('[name=frame_background]').value || '#1d2433';
      const end = cut.querySelector('[name=frame_background_end]').value;
      result.frame = {enabled:cut.querySelector('[name=frame]').checked, background:end ? [top, end] : top};
    }
    const form = document.querySelector(`.export-framing[data-export="${CSS.escape(output.value)}"]`);
    if (form) {
      if (!form.elements.focus_x.value || !form.elements.focus_y.value) throw new Error('Complete both crop positions to preview them.');
      result.framing = {fit:form.elements.fit.value, focus:[Number(form.elements.focus_x.value) / 100, Number(form.elements.focus_y.value) / 100],
        display_width:Number(form.elements.display_width.value)};
    }
    return {beat:panel.dataset.beat, draft:result};
  };
  const render = async (serial, attempt = 0) => {
    if (serial !== generation || document.body.dataset.jobRunning === '1') return;
    const revision = document.body.dataset.revision;
    let candidate;
    try {
      const fields = draft();
      controller = new AbortController();
      status.textContent = 'Updating layout still…';
      const response = await fetch('still', {method:'POST', headers:{'Content-Type':'application/json'}, signal:controller.signal,
        body:JSON.stringify({run_id:document.body.dataset.run, binding:document.body.dataset.binding, revision,
          export:Number(output.value), ...fields})});
      if (serial !== generation || revision !== document.body.dataset.revision) return;
      if (!response.ok) {
        const message = await response.text();
        if (message.startsWith('Still preview busy') && attempt < 30) {
          timer = setTimeout(() => render(serial, attempt + 1), 250); return;
        }
        throw new Error(message);
      }
      const blob = await response.blob();
      candidate = URL.createObjectURL(blob);
      const decoded = new Image(); decoded.src = candidate; await decoded.decode();
      if (serial !== generation || revision !== document.body.dataset.revision) { URL.revokeObjectURL(candidate); return; }
      const previous = url; url = candidate; image.src = url;
      image.alt = 'Layout still for step ' + fields.beat + ', using this recording';
      image.dataset.beat = fields.beat;
      image.dataset.renderMs = response.headers.get('X-Reshoot-Preview-Ms') || '';
      image.dataset.sha256 = response.headers.get('ETag') || '';
      image.dataset.revision = revision;
      ready = true; view();
      if (previous) URL.revokeObjectURL(previous);
      const unsaved = !!document.querySelector('[data-unsaved]');
      status.textContent = (unsaved ? 'Unsaved layout still. ' : 'Layout still from this recording. ') + 'Update preview makes the video.';
    } catch (error) {
      if (candidate && candidate !== url) URL.revokeObjectURL(candidate);
      if (serial === generation && error.name !== 'AbortError') {
        status.textContent = error.message;
        if (image.dataset.beat !== document.querySelector('.beat.selected')?.dataset.beat) { wantStill = false; view(); }
      }
    }
  };
  const schedule = (activate = false) => {
    generation++; clearTimeout(timer); controller?.abort();
    wantStill ||= activate;
    const serial = generation;
    timer = setTimeout(() => render(serial), 240);
  };
  document.addEventListener('reshoot:step-selected', () => schedule(true));
  document.addEventListener('reshoot:sources-saved', () => schedule());
  document.addEventListener('reshoot:project-state', () => schedule());
  document.addEventListener('reshoot:show-recording', () => { wantStill = false; view(); });
  document.querySelectorAll('.beat input[name=caption], .beat input[name=sub], .look input, .look select, .cut [name=frame], .cut [name=frame_background], .cut [name=frame_background_end], .export-framing input, .export-framing select').forEach(input => {
    input.addEventListener('input', () => {
      const form = input.closest('.export-framing'); if (form) output.value = form.dataset.export;
      schedule(true);
    });
    input.addEventListener('change', () => schedule(true));
  });
  output.onchange = () => schedule(true);
  toggle.onclick = () => { wantStill = !wantStill; view(); };
  window.addEventListener('pagehide', () => { generation++; controller?.abort(); clearTimeout(timer); if (url) URL.revokeObjectURL(url); });
  schedule();
})();
