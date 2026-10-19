"""For the tests: SETUP runs before recording, and beats follow links between pages."""
SETUP = [("visit", "await __demo.click('#about')", 0.3), ("mark", "sessionStorage.seen = location.pathname", 0)]
BEATS = [
    ("home", "if (sessionStorage.seen !== '/about.html') throw new Error('SETUP did not run')", 0.5),
    ("about", "await __demo.click('#about')", 0.5),
    ("check", "if (location.pathname !== '/about.html' || typeof __demo !== 'object') throw new Error('not on the new page')", 0.3),
    ("back", "await __demo.click('#back')", 0.5),
]
