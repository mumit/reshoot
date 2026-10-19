"""For the tests: BLUR from the start, then blur() and unblur() during the take."""
BLUR = ["#list li small"]
BEATS = [
    ("start", "if (getComputedStyle(document.querySelector('#list li small')).filter !== 'blur(12px)') throw new Error('BLUR not applied')", 0.5),
    ("blur", "__demo.blur('h1', { px: 8 }); if (getComputedStyle(document.querySelector('h1')).filter !== 'blur(8px)') throw new Error('blur() not applied')", 0.5),
    ("added", "document.querySelector('#text').value = 'x'; document.querySelector('#add').requestSubmit(); await __demo.sleep(100); if ([...document.querySelectorAll('#list li small')].some(e => getComputedStyle(e).filter !== 'blur(12px)')) throw new Error('a new note is not blurred')", 0.5),
    ("unblur", "__demo.unblur('h1'); if (getComputedStyle(document.querySelector('h1')).filter !== 'none') throw new Error('unblur() did not undo it')", 0.5),
    ("bad", "try { __demo.blur('#('); throw new Error('a bad selector was accepted') } catch (e) { if (e.message.includes('accepted')) throw e }", 0.3),
]
