// Stable alternatives for recording and explicit repair. Positional paths are only a last resort for a picked
// element, never an automatic repair suggestion.
(() => {
  const css = text => CSS.escape(text);
  const unique = selector => { try { return document.querySelectorAll(selector).length === 1; } catch { return false; } };
  const generated = text => /\d{3,}|^[a-z]+-[a-z0-9]{5,}$|^:r|^r:|[A-Z0-9]{6,}/.test(text);
  const words = element => (element.innerText || '').trim().replace(/\s+/g, ' ');
  window.__reshootTargets = element => {
    const targets = [], tag = element.tagName.toLowerCase();
    for (const attr of ['data-testid', 'data-test', 'data-cy', 'data-qa']) {
      const value = element.getAttribute(attr), selector = value && `[${attr}="${css(value)}"]`;
      if (selector && unique(selector)) targets.push({css: selector});
    }
    if (element.id && !generated(element.id) && unique('#' + css(element.id))) targets.push({css: '#' + css(element.id)});
    const name = element.getAttribute('aria-label') || (element.labels && element.labels[0] ? words(element.labels[0]) : '') || words(element);
    const role = element.getAttribute('role') || ({button: 'button', a: 'link', textarea: 'textbox', select: 'combobox'})[tag]
      || (tag === 'input' ? ({checkbox: 'checkbox', radio: 'radio', button: 'button', submit: 'button'})[element.type] || 'textbox' : null);
    if (role && name && name.length <= 100) targets.push({role, name});
    for (const attr of ['name', 'aria-label', 'placeholder', 'title']) {
      const value = element.getAttribute(attr), selector = value && `${tag}[${attr}="${css(value)}"]`;
      if (selector && unique(selector)) targets.push({css: selector});
    }
    const text = words(element);
    if (text && text.length <= 100 && [...document.querySelectorAll(tag)].filter(e => words(e) === text).length === 1)
      targets.push({css: tag, text});
    return targets.filter((value, i) => targets.findIndex(other => JSON.stringify(value) === JSON.stringify(other)) === i).slice(0, 12);
  };
  window.__reshootPath = element => {
    const parts = [];
    for (let node = element; node && node !== document.documentElement; node = node.parentElement) {
      const siblings = node.parentElement ? [...node.parentElement.children].filter(n => n.tagName === node.tagName) : [node];
      parts.unshift(node.tagName.toLowerCase() + (siblings.length > 1 ? `:nth-of-type(${siblings.indexOf(node) + 1})` : ''));
    }
    return 'html > ' + parts.join(' > ');
  };
})();
