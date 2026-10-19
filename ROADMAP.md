# Roadmap

What I'd like reshoot to do next, most important first. The aim is demos that stay current without anyone
re-recording them, and fewer reasons to reach for a screen recorder instead.

Each item says what it is and why it matters. When one ships, move it to Done with a line on what it does.

## Next

1. **Reshoot in CI.** A GitHub Action that records the takes again on each release and opens a pull request with
   the new video and GIFs. When a selector breaks, the run fails and names the beat, so a stale README GIF is found
   before anyone sees it. It needs one command that runs a whole shoot (start the app, record each take, cut,
   check), which is useful on its own too. The check by eye stays: the pull request carries the review sheets, and
   a person merges it.
   *Status: `reshoot run`, `action.yml` and an example workflow are built and work on macOS. Not yet run on
   GitHub's Linux runners.*
2. **Zoom on clicks.** The view zooms in on what's being clicked or typed, then pans back out. reshoot knows where
   every click lands, so it can do this exactly. Without it, a full-width page is hard to read on a phone.
3. **Write the storyboard by clicking.** `reshoot rec URL` opens Chrome in a window, records clicks and typing, and
   writes beats with stable selectors. Captions and holds are then edited by hand. An importer for Playwright tests
   would help teams that already have them.
4. **Automatic privacy checks before the look.** Read the text in frames and flag emails, keys, tokens, phone
   numbers and file paths. Detect faces. Add `__demo.blur(sel)` to blur part of a page during a take. The check by
   eye stays; this points it at likely problems first.
5. **Subtitles and voiceover.** Write the captions to an `.srt` file, since most sites play videos muted. Add an
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

- **First release:** `reshoot web`, `window`, `check`, `gif`, `last-change` and `edit`; the guide; six Claude Code
  skills; the notes example.
