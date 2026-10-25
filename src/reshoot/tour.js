(() => {
  const steps = [...document.querySelectorAll('.step')], links = [...document.querySelectorAll('[data-step]')];
  const status = document.getElementById('progress');
  let current = -1;
  const show = (index, focus = true) => {
    current = Math.max(0, Math.min(steps.length - 1, index));
    steps.forEach((step, i) => step.hidden = i !== current);
    links.forEach(link => {
      if (+link.dataset.step === current) link.setAttribute('aria-current', 'step');
      else link.removeAttribute('aria-current');
    });
    status.textContent = `Step ${current + 1} of ${steps.length}`;
    if (focus) { steps[current].querySelector('h2').focus({preventScroll: true}); window.scrollTo({top: 0, behavior: 'instant'}); }
  };
  const fromHash = () => {
    const match = /^#step-(\d+)$/.exec(location.hash);
    const index = Math.max(0, Math.min(steps.length - 1, match ? +match[1] - 1 : 0));
    if (index !== current) show(index, current >= 0);
  };
  document.addEventListener('click', event => {
    const link = event.target.closest('[data-go]');
    if (!link) return;
    event.preventDefault();
    const index = +link.dataset.go;
    show(index);
  });
  document.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName)) return;
    const index = {ArrowRight: Math.min(steps.length - 1, current + 1), ArrowLeft: Math.max(0, current - 1), Home: 0, End: steps.length - 1}[event.key];
    if (index == null) return;
    event.preventDefault();
    show(index);
  });
  window.addEventListener('hashchange', fromHash);
  fromHash();
})();
