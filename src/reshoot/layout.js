// Bounded geometry-only samples. No page text, labels or field values leave this function.
(() => {
  const viewport = window.visualViewport;
  const width = viewport ? viewport.width : innerWidth, height = viewport ? viewport.height : innerHeight;
  const text = [], seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node, visited = 0, skippedTransforms = 0;
  while ((node = walker.nextNode()) && visited++ < 2000 && text.length < 200) {
    const element = node.parentElement;
    if (!element || !node.textContent.trim() || seen.has(element) || element.closest('script,style,noscript,#__cap,#__cur,[hidden]')) continue;
    const style = getComputedStyle(element);
    if (style.visibility !== 'visible' || style.display === 'none' || +style.opacity === 0) continue;
    const range = document.createRange(); range.selectNodeContents(node);
    const box = range.getBoundingClientRect();
    const font = parseFloat(style.fontSize);
    if (!font || box.width <= 0 || box.height <= 0 || box.right <= 0 || box.bottom <= 0 || box.left >= width || box.top >= height) continue;
    let transformed = false;
    for (let ancestor = element, depth = 0; ancestor && depth++ < 30; ancestor = ancestor.parentElement) {
      const computed = getComputedStyle(ancestor);
      if (computed.transform !== 'none') {
        const matrix = new DOMMatrixReadOnly(computed.transform);
        if (!matrix.is2D || Math.abs(matrix.a - 1) > .001 || Math.abs(matrix.d - 1) > .001 || Math.abs(matrix.b) > .001 || Math.abs(matrix.c) > .001) transformed = true;
      }
      if (computed.scale && !['none', '1', '1 1'].includes(computed.scale)) transformed = true;
      if (computed.zoom && computed.zoom !== 'normal' && +computed.zoom !== 1) transformed = true;
    }
    if (transformed) { skippedTransforms++; continue; }
    seen.add(element);
    text.push({box: [box.x, box.y, box.width, box.height], font_px: font});
  }
  return {schema_version: 1, viewport: [width, height], text, skipped_transforms: skippedTransforms,
          scope: 'sampled main-page text at the result hold'};
})();
