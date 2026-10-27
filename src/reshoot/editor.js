/* Progressive enhancement: one selected-step inspector and a keyboard filmstrip. */
(() => {
  const strip = document.getElementById('step-strip');
  const panels = [...document.querySelectorAll('#story-panel .beat')];
  if (!strip || !panels.length) return;
  const list = document.createElement('div');
  list.className = 'step-choices'; list.setAttribute('role', 'tablist'); list.setAttribute('aria-label', 'Story steps');
  let reveal = false;  // a filmstrip choice, rather than a selection from elsewhere
  const buttons = panels.map((panel, i) => {
    const button = document.createElement('button'); button.type = 'button';
    button.dataset.selectStep = panel.dataset.beat;
    button.id = `step-choice-${i}`; panel.id = `step-inspector-${i}`;
    button.setAttribute('role', 'tab'); button.setAttribute('aria-controls', panel.id);
    panel.setAttribute('role', 'tabpanel'); panel.setAttribute('aria-labelledby', button.id);
    const image = panel.querySelector('.play img');
    if (image) { const thumbnail = image.cloneNode(); thumbnail.alt = ''; thumbnail.loading = 'lazy'; button.append(thumbnail); }
    const label = document.createElement('span'); label.textContent = `${i + 1}. ${panel.dataset.name || panel.dataset.beat}`;
    button.append(label);
    button.setAttribute('aria-label', `Step ${i + 1}: ${panel.dataset.name || panel.dataset.beat}. ${panel.querySelector('.checks').textContent.trim()}`);
    button.title = panel.querySelector('.purpose')?.textContent || label.textContent;
    const choose = () => {
      reveal = true;
      document.dispatchEvent(new CustomEvent('reshoot:select-step', {detail:{id:panel.dataset.beat, seek:true}}));
    };
    button.onclick = choose;
    button.onkeydown = event => {
      const offset = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0;
      const index = event.key === 'Home' ? 0 : event.key === 'End' ? panels.length - 1 : (i + offset + panels.length) % panels.length;
      if (!offset && !['Home', 'End'].includes(event.key)) return;
      event.preventDefault(); buttons[index].focus(); buttons[index].click();
    };
    list.append(button);
    return button;
  });
  strip.append(list); strip.hidden = false; document.body.dataset.focused = '1';
  document.addEventListener('reshoot:step-selected', event => {
    panels.forEach((panel, i) => {
      const selected = panel.dataset.beat === event.detail.id;
      panel.hidden = !selected; buttons[i].tabIndex = selected ? 0 : -1;
      buttons[i].setAttribute('aria-selected', String(selected));
      if (selected && reveal) {
        // With the preview held in place, bring the chosen step's inspector into view beside it.
        const watch = strip.closest('.watch');
        if (watch && getComputedStyle(watch).position === 'sticky') panel.scrollIntoView({block:'nearest'});
      }
      if (selected) {
        const left = buttons[i].offsetLeft, right = left + buttons[i].offsetWidth;
        if (left < list.scrollLeft) list.scrollLeft = left;
        else if (right > list.scrollLeft + list.clientWidth) list.scrollLeft = right - list.clientWidth;
      }
    });
    reveal = false;
  });
  const initial = panels.find(panel => panel.classList.contains('selected'))?.dataset.beat ||
    document.querySelector('.failure [data-beat]')?.dataset.beat || panels[0].dataset.beat;
  document.dispatchEvent(new CustomEvent('reshoot:select-step', {detail:{id:initial, seek:false}}));
})();
