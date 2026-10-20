"""Made-up notes data. Every fresh browser resets it."""
URL = 'http://127.0.0.1:8765/'
SIZE = '1280x720@1'
BEATS = [
    ('intro', "__demo.caption('Find a note by its words')", 1.5),
    ('add', "__demo.caption(null); await __demo.type('#text', 'Pick up the bikes'); __demo.key('Enter'); await __demo.waitFor(() => document.querySelector('#list').textContent.includes('bikes'))", 1),
    ('search', "await __demo.type('#q', 'bike'); await __demo.waitFor(() => document.querySelectorAll('#list li').length === 1)", 2),
    ('end', "__demo.hide()", 0.5),
]
