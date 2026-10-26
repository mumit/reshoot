---
name: record-web
description: Record a web page or web app acting out a storyboard in headless Chrome, with a moving cursor, typing and captions, using `reshoot web`. Use for the browser part of a demo video, including phone-sized layouts.
---

# Record a web take

`reshoot web STORYBOARD OUT.mp4` opens the page in headless Chrome, plays the beats and writes `OUT.mp4` (60 fps, at the page size times the pixel ratio: 1280x720@1.5 gives 1920x1080), plus `OUT.beats.json` for cutting, `OUT.assets.json` listing every image and media URL for check-privacy, and `OUT.events.json` with each action and caption. Only the page is captured, so nothing else on the screen can show. In a project, `reshoot preview reshoot.toml` records every take smaller and faster.

## Steps

1. Start the app on demo data, on its own port.
2. Get a first storyboard:
   - **The person clicks through it:** `reshoot rec http://localhost:8000/ demo/draft.toml` opens Chrome with a fresh profile and writes the beats as they click, with suggested result checks. Keep the ones that show the result. Ask for this when the flow is long or the selectors are hard to find. For a whole project, offer `reshoot create URL --directory demo`, whose toolbar also adds captions and checks. Both wait for a person: do not start them unattended.
   - **You write it:** read the app's HTML for the selectors. Prefer test ids, ids and names.
3. Finish the storyboard: add captions, check the holds, and give the beats names the cut can use. Build it a beat at a time, recording a short take as you go.
4. Record: `reshoot web demo/storyboard.toml takes/web.mp4`. Each beat prints how long it took. A failing beat stops the take and names itself.
5. Look at frames, not only the log: `ffmpeg -ss 5 -i takes/web.mp4 -frames:v 1 frame.png`, at several times, including after each page load and near the bottom of the page.
6. For phones: `--size 390x844@3 --mobile`, or `size` and `mobile` in a second storyboard.

## TOML storyboards

Use a schema-version-1 TOML storyboard for new takes, with named `[[beat]]` entries, `[[beat.action]]` operations and `[[beat.expect]]` result checks. `reshoot init DIR` writes a complete notes example, `reshoot web --help` lists the settings, and the guide's `projects.md` lists every field. Install the `browser` extra.

- **Targets** use `css`, `test_id`, or `role` with an optional `name`, plus `text` and `frame`.
- **Actions** use native input and fail on a covered, disabled, missing or ambiguous control. Never force a click past a broken demo. For a dropdown, use `select` with the option's visible label; checkboxes and radios use `check`.
- **Result checks** wait for the result, then the hold gives reading time. A `.take.json` records each check and its frame.
- **`[caption]`** sets position, safe margin, minimum seconds, font and colours. Captions are drawn after recording as plain text, so `reshoot recut RUN` can change them.
- **`[cursor]`** sets `size` (0.5 to 3), `typing` (characters a second, default 13) and `ripple` (default true).
- **Recorded `fallbacks`** are alternative ways to find a control. They only suggest a repair; replay never swaps them in by itself. After a missing-control failure, `reshoot repair RUN` shows the suggestion, `--apply` rechecks and applies it, and `--pick` lets the owner choose the control. Then record a fresh preview.
- **`recording_issue`** marks a step the recorder couldn't replay. Write its actions and remove the field; never delete the step to make a recording pass.
- **`reshoot preview CONFIG --from BEAT`** replays the earlier beats without recording, then records from that beat. A partial preview skips the edit and scan and never replaces a final.

Narration, docs screenshots and tours are set with `reshoot audio`, `reshoot screenshot` and `reshoot tour` (see `--help`). Narration changes need a fresh recording. A screenshot or tour step must come from a beat with passing result checks: never replace a missing check with a standalone screenshot. Keep every action, expected result and scan source intact.

## Zoom on clicks

With `zoom = true` (`ZOOM = True` in Python, or `--zoom`), the view moves in on what's clicked or typed. It's worked out after recording, from where each action happened and from the frames: it stays while the next action is in view, and moves out for an action far away, a quiet spell, a new caption, or a sizeable change outside the view. A target as wide as the page isn't zoomed. Its settings: `scale` 1.8 (the most it enlarges), `lead` 0.7 s, `hold` 1.0 s, `quiet` 4 s, `show` 1 s, and `watch` (on) to look at frames for changes. Zoomed text stays sharp, captions are drawn after the zoom, and processing takes about 2.5 times the take's length.

## Python storyboards

Older takes use a Python storyboard; `../../examples/notes/storyboard.py` from this skill's folder is a full one, and `../../examples/notes/voiced.py` adds a voiceover. It sets `URL`, `SIZE`, `THEME`, `SETUP` (beats run before recording, such as a demo login), `WARM` (views to load first), `ASSETS`, `ZOOM`, `BLUR`, `VOICE` and `BEATS`. Each beat is (name, JavaScript, seconds to hold), run in the page inside an async function, with `__demo`:

| Call | Does |
|---|---|
| `await __demo.click(sel)` | glides the cursor there and clicks, with a ripple |
| `await __demo.type(sel, text, {clear: true})` | clicks the field and types at a person's pace |
| `__demo.key("Enter")` | presses a key |
| `await __demo.waitFor(sel or fn, ms)` | waits until something appears |
| `await __demo.scroll(dy, {sel})` | scrolls smoothly |
| `await __demo.to(sel)` / `moveTo(x, y)` | moves the cursor without clicking |
| `__demo.caption(text, small)` / `caption(null)` | shows or hides a caption |
| `__demo.hide()` / `show()` | hides or shows the cursor |
| `__demo.blur(sel, {px})` / `unblur(sel)` | blurs everything matching sel, including what the page adds later |
| `__demo.byText(tag, text)` | the element whose words are text, to pass to `click` |
| `__demo.zoom(sel, {scale})` / `zoomOut()` | zooms in on sel until `zoomOut()`, over the automatic zoom |

`VOICE` maps beat names to narration; each beat waits for its line. `VOICE_ENGINE = "kokoro --voice af_heart"` selects [optional local neural speech](../../guide/install.md#local-neural-narration). Audition with `reshoot audio audition BEAT --project demo`. Otherwise the default is macOS `say` or Linux `espeak-ng`. Custom commands read stdin and need `{out}`. Python stories use older overlay input, so they cannot claim TOML's native-input checks.

## Pitfalls

- **Waiting for results.** A fixed hold that works once is too short the next time. Wait for the result first.
- **Blank views when first shown.** Each take starts with a fresh profile, so nothing is cached. Load slow views first (`WARM` in Python).
- **Something private on every page,** such as an account name: blur it for the whole take.
- **Logged out.** Log in with a demo account before recording. Never point reshoot at someone's own browser profile.
- **Random content** differs each take, so check every take.
- **Zoom hides a small result** that doesn't count as a change, such as a short line of text. Zoom out in the beat that shows it.
- **Zooming in and out too often** usually means a long hold: shorten it, or raise `quiet`.
- **A recorded storyboard is a draft.** Read its selectors: one that matches by position breaks first.
- **A link to a new page** keeps the overlay, caption and cursor. In Python, code after the click in the same beat doesn't run: put it in the next beat.
- **Page errors** are printed at the end and fail the take. They often mean a beat ran before the page was ready.
