# Roadmap

What I'd like reshoot to do next, most important first. The aim is demos that stay current without anyone
re-recording them, and fewer reasons to reach for a screen recorder instead.

Each item says what it is and why it matters. When one ships, move it to Done with a line on what it does.

## Next

1. **Trim dead time.** In the finished video, shorten pauses where nothing moves (to about 0.8 s), and shift the
   beat times to match. Recordings made by a person are full of pauses spent finding the next button.
2. **Export presets** for X, LinkedIn, YouTube and README GIFs: each site's size, length and format, and a poster
   frame.
3. **iOS and Android takes:** the iOS Simulator (`xcrun simctl io recordVideo`) and the Android emulator
   (`adb screenrecord`), driven by a script like a storyboard. Both can be recorded without showing the desktop.

## Later

- **Frames and themes:** a browser frame, a phone frame, a background, brand colours and a logo, set once for a
  project.
- **An edit file instead of an edit script:** a short list of parts in YAML or TOML, for people who'd rather not
  write Python.
- **A Playwright importer:** turn existing Playwright tests into storyboards.
- **Faster tries:** `--from BEAT` to start a take part-way, and a quick low-resolution mode.
- **Translations:** one storyboard with captions in several languages.
- **Faces and people on Linux:** a detector that doesn't need macOS, such as OpenCV's.
- **Linux and Windows:** try every part, fix what breaks, and say what works.

## Done

- **Subtitles and voiceover:** `VOICE` in a storyboard speaks a line as each beat starts (macOS `say`, `espeak-ng`,
  or any command), and each beat waits for its line. The cut adds the voice and optional music that ducks under it
  and fades out, and writes an `.srt` from the voiceover or the captions.
- **Automatic privacy checks:** `reshoot check` scans supplied images and sampled frames for emails, phone numbers, keys, paths
  with a user name, street addresses and watch-for words (Vision on macOS, Tesseract elsewhere), and for faces and
  people (macOS). Flags come first on the sheets, boxed in red, with what was found masked in the output.
  `BLUR` and `__demo.blur(sel)` hide what has to stay in the app.
- **Write the storyboard by clicking:** `reshoot rec URL OUT.py` opens Chrome with a fresh profile and writes a
  beat for each click and run of typing, with stable selectors and holds from the pauses. Passwords become a
  placeholder.
- **Zoom on clicks:** `ZOOM = True` or `--zoom`. The view moves in on clicks and typing, worked out after
  recording so it lands on each click. It stays through pauses while the next action is in view, and moves out for
  a long quiet spell, a new caption, an action far away, or a change outside the view (seen in the frames).
  Captions are drawn after the zoom. `__demo.zoom()` and `zoomOut()` for exact control.
- **Reshoot in CI:** `reshoot run` does a whole shoot from a `reshoot.toml`, and `action.yml` runs it on GitHub's
  Linux and macOS runners. The example workflow reshoots on each release and opens a pull request with the new
  files for a person to check. reshoot reshoots its own notes example this way.
- **First release:** `reshoot web`, `window`, `check`, `gif`, `last-change` and `edit`; the guide; six Claude Code
  skills; the notes example.
