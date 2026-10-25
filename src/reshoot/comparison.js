(() => {
  const panel = document.getElementById('compare-panel');
  const select = document.getElementById('comparison-source');
  if (!panel || !select) return;
  const results = document.getElementById('comparison-results');
  const status = document.getElementById('comparison-status');
  const current = document.body.dataset.run, binding = document.body.dataset.binding;
  let request = 0, loaded = false;
  const node = (tag, text, className) => {
    const element = document.createElement(tag);
    if (text != null) element.textContent = text;
    if (className) element.className = className;
    return element;
  };
  const link = (text, href) => {
    const element = node('a', text);
    element.href = href; element.target = '_blank'; element.rel = 'noopener';
    return element;
  };
  const load = async () => {
    const sequence = ++request, previous = select.value;
    const previousBinding = select.selectedOptions[0].dataset.binding;
    results.replaceChildren(); results.setAttribute('aria-busy', 'true');
    status.textContent = 'Loading the two chosen recordings…';
    loaded = true;
    try {
      const query = new URLSearchParams({run_id:current, binding, previous_id:previous, previous_binding:previousBinding});
      const response = await fetch('comparison.json?' + query, {cache:'no-store'});
      const data = await response.json();
      if (sequence !== request || previous !== select.value) return;
      if (!response.ok) throw new Error(data.error || 'Could not compare these recordings.');
      const headers = node('div', null, 'compare-run-links');
      for (const side of ['previous', 'current']) {
        const run = data[side], box = node('div');
        box.append(node('strong', `${side === 'previous' ? 'Previous' : 'Current'} ${run.id.slice(0,8)} · ${run.mode}`));
        box.append(node('p', run.status), link('Open review evidence', run.review));
        headers.append(box);
      }
      results.append(headers, node('p', data.note, 'hint'));
      for (const row of data.beats) {
        const article = node('article', null, 'compare-beat'); article.dataset.beat = row.beat;
        article.append(node('h3', row.beat));
        const flags = [];
        if (row.change === 'added') flags.push('Added step');
        if (row.change === 'removed') flags.push('Removed step');
        if (row.frame_changed === true) flags.push('Frame file changed');
        if (row.frame_changed === false) flags.push('Same captured frame');
        if (row.definition_changed) flags.push('Task definition changed');
        if (row.results_changed) flags.push('Result details changed');
        article.append(node('p', flags.join(' · ') || 'Checked frame unavailable on one side.', 'hint'));
        const pair = node('div', null, 'compare-pair');
        for (const side of ['previous', 'current']) {
          const beat = row[side], figure = node('figure'); figure.dataset.side = side;
          const label = side === 'previous' ? 'Previous' : 'Current';
          if (!beat) {
            figure.append(node('figcaption', label + ': step absent'));
          } else {
            figure.append(node('figcaption', `${label}: ${beat.purpose} · ${beat.status}`));
            if (beat.frame) {
              const image = node('img'); image.src = beat.frame.src;
              image.alt = label + ': ' + beat.purpose; image.loading = 'lazy';
              image.addEventListener('error', () => {
                image.remove(); figure.append(node('p', 'This pinned frame could not be loaded. Refresh the comparison.'));
              });
              figure.append(image, node('p', `${beat.frame.checks} passing result check${beat.frame.checks === 1 ? '' : 's'}`));
              figure.append(link('Open frame at image size', beat.frame.src));
            } else {
              figure.append(node('p', beat.reason));
            }
          }
          pair.append(figure);
        }
        article.append(pair); results.append(article);
      }
      status.textContent = data.beats.length ? `Compared ${data.beats.length} result-check steps.` : 'No checked browser result frames are available in these recordings.';
    } catch (error) {
      if (sequence === request) { results.replaceChildren(); status.textContent = error.message; }
    } finally {
      if (sequence === request) results.setAttribute('aria-busy', 'false');
    }
  };
  panel.addEventListener('toggle', () => { if (panel.open && !loaded) load(); });
  select.addEventListener('change', load);
  document.getElementById('compare-refresh').addEventListener('click', load);
})();
