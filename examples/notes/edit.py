"""Cuts the notes example into a finished video: the web take up to its end beat, then the terminal take (if given)
on a card with a label, then an end card. Also a 9:16 version, one GIF, and subtitles. If the web take has a
voiceover (VOICE in its storyboard, as in voiced.py), it's added, with music under it if MUSIC is set. A starting
point for your own edit script.

    reshoot edit examples/notes/edit.py takes/notes.mp4 [takes/terminal.mp4]

Writes notes-final.mp4, notes-vertical.mp4, notes.gif and notes-final.srt next to the web take.
"""
import shutil, sys, tempfile
from pathlib import Path

from reshoot import cut

# The words on screen
TITLE, TAGLINE = "Notes", "a made-up app for trying reshoot"
TERMINAL = "Or from the terminal"
BG, GREY, ACCENT = (14, 13, 12), (170, 170, 170), (245, 180, 60)
W, H = 1920, 1080  # every part is this size, so they can be joined
MUSIC = None  # a sound file to play quietly under the video, such as "tools/demo/music.m4a"


def main(web, terminal=None):
    web = Path(web)
    b = cut.beats(web)
    out = web.parent
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        parts = [cut.trim(web, 0, b["end"], t / "web.mp4", fade_out=0.4)]  # the take's own end card is replaced below

        if terminal:
            # Cut where it finished (plus a moment to read the result), on a card with a label. The terminal is
            # 1280x720, so it's placed at a width that leaves room for the label.
            done = cut.last_change(terminal) + 1.2
            term = cut.trim(terminal, 0, done, t / "term-cut.mp4", fade_in=0.3)
            card = cut.Card(W, H, BG).text(None, 70, TERMINAL, 56, 700).save(t / "term-bg.png")
            parts.append(cut.place(card, term, (W - 1500) // 2, 170, t / "term.mp4", width=1500))

        end = cut.Card(W, H, BG).text(None, 420, TITLE, 112, 700).text(None, 580, TAGLINE, 44, 500, GREY)
        parts.append(cut.still(end.save(t / "end.png"), 3, t / "end.mp4"))
        silent = cut.concat(parts, t / "silent.mp4")

        # The web part starts the video, so its voiceover lines and subtitles keep their times (offset 0)
        said = cut.lines(web, 0, b["end"])
        final, voice = out / "notes-final.mp4", t / "voice.wav"
        if said or MUSIC:
            cut.add_audio(silent, final, voice=said and cut.voice_track(said, voice, cut.duration(silent)), music=MUSIC)
        else:
            shutil.copyfile(silent, final)
        cut.write_srt(cut.cues(web, 0, b["end"]), out / "notes-final.srt")

        tall = cut.Card(1080, 1920, BG).text(None, 520, TITLE, 84, 700).text(None, 1360, TAGLINE, 36, 500, ACCENT)
        vertical = cut.vertical(silent, tall.save(t / "tall.png"), t / "vertical.mp4")
        if said or MUSIC:
            cut.add_audio(vertical, out / "notes-vertical.mp4", voice=said and voice, music=MUSIC)
        else:
            shutil.copyfile(vertical, out / "notes-vertical.mp4")
    cut.gif(web, b["type"], b["end"] - 0.1, out / "notes.gif")
    for f in ("notes-final.mp4", "notes-vertical.mp4", "notes.gif", "notes-final.srt"):
        print(f"  {out / f}" + (f"  {cut.duration(out / f):5.1f}s" if not f.endswith(".srt") else ""))


if __name__ == "__main__":
    main(*(sys.argv[1:] or ["takes/notes.mp4"]))
