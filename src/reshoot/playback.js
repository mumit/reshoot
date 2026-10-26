/* Paired exports keep their own timing. Step appearances come from the saved cut maps. */
window.reshootPlayback = (host, data) => {
  const node = (tag, text) => { const el = document.createElement(tag); if (text != null) el.textContent = text; return el; };
  if (!data.previous.videos.length || !data.current.videos.length) {
    host.append(node('p', 'Paired playback needs an exported MP4 or MOV in both recordings. The checked frames and review pages remain available.'));
    return () => {};
  }
  host.className = 'compare-playback';
  host.append(node('h3', 'Watch the exports'));
  host.append(node('p', 'Play both starts the videos together. Each keeps its recorded timing. Choose a step to compare its appearances in the two cuts.'));
  const pair = node('div'); pair.className = 'compare-pair';
  const sides = [];
  const primaryName = data.current.videos[0].name;
  for (const kind of ['previous', 'current']) {
    const run = data[kind], label = kind === 'previous' ? 'Previous' : 'Current';
    const figure = node('figure'); figure.dataset.side = kind;
    const choice = node('select'), field = node('label', label + ' export');
    choice.setAttribute('aria-label', label + ' export');
    choice.className = 'playback-export';
    run.videos.forEach((video, i) => {
      const basename = video.name.split('/').pop();
      const repeated = run.videos.filter(other => other.name.split('/').pop() === basename).length > 1;
      const option = node('option', repeated ? video.name : basename); option.value = i; choice.append(option);
    });
    const match = run.videos.findIndex(video => video.name === primaryName);
    choice.value = match < 0 ? 0 : match;
    field.append(choice);
    const video = node('video'); video.controls = true; video.preload = 'metadata'; video.playsInline = true;
    video.setAttribute('aria-label', label + ' export from ' + run.id.slice(0, 8));
    const note = node('p'); note.className = 'hint'; note.setAttribute('role', 'status');
    figure.append(node('figcaption', `${label} ${run.id.slice(0, 8)} · ${run.mode}`), field, video, note); pair.append(figure);
    sides.push({kind, run, choice, video, note, selected: null, stop: null, failed: false});
  }
  host.append(pair);
  const controls = node('div'); controls.className = 'playback-controls';
  const listen = node('select'), audioField = node('label', 'Listen to');
  listen.setAttribute('aria-label', 'Listen to');
  for (const [value, text] of [['current', 'Current'], ['previous', 'Previous'], ['none', 'Mute both']]) {
    const option = node('option', text); option.value = value; listen.append(option);
  }
  audioField.append(listen);
  const playBoth = node('button', 'Play both'), pauseBoth = node('button', 'Pause both');
  const steps = node('select'), stepField = node('label', 'Step in the cut'); steps.className = 'playback-step'; stepField.append(steps);
  steps.setAttribute('aria-label', 'Step in the cut');
  const jump = node('button', 'Go to step'), playStep = node('button', 'Play step');
  for (const button of [playBoth, pauseBoth, jump, playStep]) button.type = 'button';
  const transport = node('div'), stepping = node('div');
  transport.className = stepping.className = 'playback-buttons';
  transport.append(playBoth, pauseBoth); stepping.append(jump, playStep);
  const whole = node('div'), byStep = node('div');
  whole.append(audioField, transport); byStep.append(stepField, stepping);
  controls.append(whole, byStep); host.append(controls);
  const status = node('p'); status.className = 'hint'; status.setAttribute('role', 'status'); host.append(status);
  const pause = () => sides.forEach(side => side.video.pause());
  const pauseMain = () => document.getElementById('video')?.pause();
  const audio = () => sides.forEach(side => { side.video.muted = listen.value !== side.kind; });
  const buttons = () => {
    const ready = sides.every(side => side.ready && !side.failed);
    playBoth.disabled = !ready; jump.disabled = playStep.disabled = !ready || !steps.value;
  };
  const start = async video => {
    try { await video.play(); }
    catch (_) { if (host.isConnected) status.textContent = 'Playback did not start. Use the video controls or try Play both again.'; }
  };
  const seek = (playing = false) => {
    if (!steps.value) return;
    pause();
    const [key, occurrence] = JSON.parse(steps.value);
    audio();
    for (const side of sides) {
      const range = side.selected.beats[key]?.[occurrence];
      side.stop = null;
      side.video.hidden = !range;
      if (!range) { side.note.textContent = 'This appearance is not in this export.'; continue; }
      if (side.failed || !side.ready) continue;
      if (range[1] > side.video.duration + .15) {
        side.note.textContent = 'The saved step timing does not fit this video. Use its controls to inspect it.';
        continue;
      }
      side.video.currentTime = range[0]; side.stop = range[1];
      side.note.textContent = `${key} · appearance ${occurrence + 1} · ${range[0].toFixed(1)} to ${range[1].toFixed(1)} s`;
      if (playing) start(side.video);
    }
    status.textContent = 'Appearances are paired by their order in each cut. Each side stops at its own step end.';
  };
  const stepChoices = () => {
    const previous = steps.value;
    steps.replaceChildren();
    const placeholder = node('option', 'Choose a step'); placeholder.value = ''; steps.append(placeholder);
    const keys = new Set(sides.flatMap(side => Object.keys(side.selected.beats)));
    for (const key of keys) {
      const count = Math.max(...sides.map(side => side.selected.beats[key]?.length || 0));
      for (let i = 0; i < count; i++) {
        const option = node('option', key + (count > 1 ? ` · appearance ${i + 1}` : ''));
        option.value = JSON.stringify([key, i]); steps.append(option);
      }
    }
    if ([...steps.options].some(option => option.value === previous)) steps.value = previous;
    status.textContent = keys.size ? 'Choose a step to seek both exports, or play the whole videos.' :
      'Step seeking needs a saved export timeline. Use the video controls to compare these recordings.';
    buttons();
  };
  const source = side => {
    pause(); side.selected = side.run.videos[Number(side.choice.value)];
    side.stop = null; side.failed = false; side.ready = false; side.video.hidden = false;
    side.note.textContent = side.selected.note || 'Loading the recorded export…';
    side.video.src = side.selected.src;
  };
  sides.forEach(side => {
    side.choice.onchange = () => { source(side); stepChoices(); audio(); };
    side.video.addEventListener('loadedmetadata', () => {
      if (!host.isConnected) return;
      side.ready = true;
      side.note.textContent = side.selected.note || 'Ready to compare.';
      buttons(); if (steps.value) seek();
    });
    side.video.addEventListener('timeupdate', () => {
      if (side.stop != null && side.video.currentTime >= side.stop) { side.video.pause(); side.stop = null; }
    });
    side.video.addEventListener('play', pauseMain);
    side.video.addEventListener('volumechange', () => {
      if (!side.video.muted) {
        listen.value = side.kind;
        sides.filter(other => other !== side).forEach(other => { other.video.muted = true; });
      }
    });
    side.video.addEventListener('error', () => {
      if (!host.isConnected) return;
      side.failed = true; pause(); side.note.textContent = 'This pinned export could not be loaded. Refresh the comparison.'; buttons();
    });
    source(side);
  });
  audio(); stepChoices();
  listen.onchange = audio;
  playBoth.onclick = () => {
    audio(); status.textContent = 'Playing each export with its own timing.';
    sides.forEach(side => { side.stop = null; side.video.hidden = false; side.note.textContent = side.selected.note || ''; start(side.video); });
  };
  pauseBoth.onclick = pause;
  steps.onchange = () => { buttons(); seek(); };
  jump.onclick = () => seek(); playStep.onclick = () => seek(true);
  const panel = host.closest('details');
  const toggle = () => { if (!panel.open) pause(); };
  panel.addEventListener('toggle', toggle);
  return () => { pause(); panel.removeEventListener('toggle', toggle); sides.forEach(side => { side.video.removeAttribute('src'); side.video.load(); }); };
};
