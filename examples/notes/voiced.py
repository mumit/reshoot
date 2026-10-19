"""The notes example with a voiceover: the same beats, and a line for some of them. Each beat waits for its line
to finish, so the take is a little longer than the silent one.

    reshoot web examples/notes/voiced.py takes/voiced.mp4
    reshoot edit examples/notes/edit.py takes/voiced.mp4 takes/terminal.mp4
"""
import runpy
from pathlib import Path

board = runpy.run_path(str(Path(__file__).with_name("storyboard.py")))
URL, SIZE, ZOOM, BEATS = board["URL"], board["SIZE"], board["ZOOM"], board["BEATS"]

VOICE = {
    "home": "Notes keeps your lists in one place.",
    "type": "Type a note,",
    "add": "and add it.",
    "search": "Search finds it as you type.",
}
