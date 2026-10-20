---
name: check-privacy
description: Check everything a demo video's takes can show (images the page loaded, frames of each take, anything picked at random) by eye on numbered contact sheets with `reshoot check`, before anything is cut or shared. Use after recording and before cutting or posting.
---

# Check a take for private things

Every image a take can show is looked at by a person, at full size, before the video is cut. This is the step that
keeps a face, a name or a house number out of a public video.

## Steps

1. Make sheets of everything not checked yet:

   ```bash
   reshoot check takes/web.assets.json takes/web.mp4 takes/cli.mp4 --review takes/review
   ```

   Add `--watch-for "Acme,Jane Roe"` (or `--watch-for @words.txt`) with anything of the person's that mustn't
   show: their name, company, street, customers. Sources can be `.assets.json` lists, videos (a frame every
   `--every` seconds, default 3), image files, folders and URLs. The app must still be running, since the assets list holds its URLs. Add anything the app could pick at
   random during a take (suggestions, featured items, a shuffled gallery): the whole set, not only what this take
   showed.
2. Start with what the scan flagged. It reads the text in supplied images and sampled frames, and flags emails, phone numbers,
   keys and tokens, file paths with a user name, street addresses and the watch-for words. On macOS it also finds
   faces and people. Flagged images come first, with a red label and a red box round each find, and are listed
   with what was found masked (`jane•••`), so nothing private lands in a log.
3. Look at every sheet (`takes/review/01.jpg` and on) at full size, flagged or not. The scan misses things: text in
   pictures, small or odd fonts, and anything it has no rule for. You may look too, but the person decides. Show
   them the sheets.
4. For any that fail: `reshoot check --review takes/review --fail 3-2 7-1`. It lists where each came from. Take those
   out of the demo data, then record the take again, since the take still shows them.
5. When the rest pass: `reshoot check --review takes/review --ok`. Passed images are remembered by a hash of their
   bytes, so the next round shows only what's new.
6. Repeat until `reshoot check` says everything has been checked.

## What fails an image

- A person: faces, heads at the edge of the frame, tiny figures far away, reflections in glass, people behind
  windows.
- Personal details: names, emails, phone numbers, addresses, number plates, house numbers, documents.
- Secrets: keys, tokens, passwords, URLs with tokens in them.
- Work details: customers, colleagues, internal tools, unreleased features, private repo names.
- The computer itself: user names, file paths, other apps, browser tabs, bookmarks, notifications.

When in doubt, it fails. In a photo app's demo, a first check missed a straw hat at the edge of a frame, a
silhouette in a mesh railing and a blurred head in the background.

## Pitfalls

- **Random picks.** A view that picks at random shows different things in each take. Check its whole pool, or check
  every take.
- **Deleting doesn't fix the take.** After removing a failed image from the demo data, record again.
- **Thumbnails hide things.** A small head at the edge only shows at full size. The sheets use up to 1000 px.
- **Text in the app.** The assets list covers images. Frames from the video cover everything else, so include the
  takes themselves.
- **A clean scan isn't a pass.** Only `--ok` marks images as checked, and only after a person has looked.
- **Something private that has to stay in the app:** blur it during the take with `BLUR` or `__demo.blur(sel)`
  (record-web), rather than taking it out of the demo data.
- **No scan here.** On Linux, text needs Tesseract (`apt install tesseract-ocr`), and faces and people need macOS.
  `reshoot check` says when part of the scan is off. Look extra closely then.

## Check status

`check` exits 0 when the supplied review items are accepted, 1 when human review is pending, and 2 on a check error. Read `report.json` in the review folder. A missing input or unavailable required text detector is an error, never a pass. Video frames are sampled every three seconds by default; unsampled frames are not covered. `--no-scan` explicitly skips automatic detection and still requires human review.
