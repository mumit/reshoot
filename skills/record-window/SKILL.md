---
name: record-window
description: Record one window of a macOS desktop app (never the whole screen) with `reshoot window`, for the parts of a demo video that only a native app can show.
---

# Record one app window

Use this for a native macOS app, with or without its source code. Capture one
demo window and keep the recipe for the next take.

## Rules

- **Never capture the whole screen.** A full-screen capture shows mail, messages, calendars and notifications. Always
  record one window by its id. `reshoot window` does nothing else.
- The app must show demo data only. Open the demo account, folder or document first.

## Steps

1. The app running the command needs Screen Recording permission once: System Settings, Privacy & Security, Screen
   Recording. Add the terminal or editor, then restart it.
2. Open the app on demo data, with the window on screen and not minimized. Get it to the state to show.
3. `reshoot window --list` shows the windows: id, app, title. Check the right one is there.
4. Record: `reshoot window TextEdit takes/app.mov --id ID -s 8`. Replace `ID` with the selected numeric ID and use a new output path for each take.
5. Look at a frame: `ffmpeg -ss 3 -i takes/app.mov -frames:v 1 frame.png`. Check the sidebar and title bar too:
   they often show names.

The command captures the window; it does not drive the app or add browser typing,
cursor effects, captions or result checks. Use app-specific automation or coordinate
manual input during capture. Save that script or procedure with the edit.
Export standalone media using numeric cuts; versioned web/VHS projects do not
support native takes. Compare native recordings manually.

## In the cut

The recording includes the window's shadow on a dark background. `cut.window_clip(mov, bg_png, x, y, out,
width=1200)` crops it to the window, rounds the corners to match the window's own, and places it on a card. A square
crop alone shows the dark background at each corner, which stands out on a light card. `cut.window_box(mov)` and
`cut.corner_radius(mov)` give the measurements, if you need them for something else.

## Pitfalls

- "could not create image from window" means the permission is missing, or the window isn't on screen.
- An app driven by a script (AppleScript, a take running at the same time) can stall. Let the other script finish
  before recording.
- Windows move between runs. The id changes each time the app restarts, so look it up each take.
