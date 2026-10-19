"""The notes example: add a note, then find it. About 15 seconds.

    python3 -m http.server 8000 --directory examples/notes     # in one terminal
    reshoot web examples/notes/storyboard.py takes/notes.mp4   # in another
"""

URL = "http://localhost:8000/"
SIZE = "1280x720@1.5"
ZOOM = True  # zoom in on the typing and clicks, then back out

BEATS = [
    ("home", "__demo.caption('Notes that are easy to find')", 1.8),
    ("type", "__demo.caption(null); await __demo.type('#text', 'Pick up the bikes from the shop')", 0.4),
    ("add", "await __demo.click('#add button'); await __demo.waitFor(() => document.querySelector('#list li')?.textContent.includes('bikes'))", 1.4),
    ("search", "__demo.caption('Search as you type'); await __demo.type('#q', 'bike')", 2.0),
    ("end", "__demo.caption('Notes', 'a made-up app for trying reshoot'); __demo.hide()", 2.5),
]
