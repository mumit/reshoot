# Roadmap

What I'd like reshoot to do next, most important first. The aim is demos that stay current without anyone
re-recording them, and fewer reasons to reach for a screen recorder instead.

Each item says what it is and why it matters. When one ships, move it to Done with a line on what it does.

## Next

1. **Write the storyboard by clicking.** `reshoot rec URL` opens Chrome in a window, records clicks and typing, and
   writes beats with stable selectors. Captions and holds are then edited by hand. An importer for Playwright tests
   would help teams that already have them.
2. **Automatic privacy checks before the look.** Read the text in frames and flag emails, keys, tokens, phone
   numbers and file paths. Detect faces. Add `__demo.blur(sel)` to blur part of a page during a take. The check by
   eye stays; this points it at likely problems first.
3. **Subtitles and voiceover.** Write the captions to an `.srt` file, since most sites play videos muted. The
   captions and their times are already in each take's `.events.json`. Add an
   optional voiceover from text, timed to the beats, and music that gets quieter under it.

## Later

- **Export presets** for X, LinkedIn, YouTube and README GIFs: each site's size and length limits, and a poster
  frame.
- **Frames and themes:** a browser frame, a phone frame, a background, brand colours and a logo, set once for a
  project.
- **An edit file instead of an edit script:** a short list of parts in YAML or TOML, for people who'd rather not
  write Python.
- **More kinds of take:** the iOS Simulator (`xcrun simctl io recordVideo`) and the Android emulator
  (`adb screenrecord`). Both can be scripted and never show the desktop.
- **Faster tries:** `--from BEAT` to start a take part-way, and a quick low-resolution mode.
- **Translations:** one storyboard with captions in several languages.
- **Linux and Windows:** try every part, fix what breaks, and say what works.

## Done

- **Zoom on clicks:** `ZOOM = True` or `--zoom`. The view moves in on clicks and typing and back out, worked out
  after recording so it lands on each click; actions close together share one view; captions are drawn after the
  zoom. `__demo.zoom()` and `zoomOut()` for exact control.
- **Reshoot in CI:** `reshoot run` does a whole shoot from a `reshoot.toml`, and `action.yml` runs it on GitHub's
  Linux and macOS runners. The example workflow reshoots on each release and opens a pull request with the new
  files for a person to check. reshoot reshoots its own notes example this way.
- **First release:** `reshoot web`, `window`, `check`, `gif`, `last-change` and `edit`; the guide; six Claude Code
  skills; the notes example.
