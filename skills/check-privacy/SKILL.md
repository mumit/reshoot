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

   Sources can be `.assets.json` lists, videos (a frame every `--every` seconds, default 3), image files, folders
   and URLs. The app must still be running, since the assets list holds its URLs. Add anything the app could pick at
   random during a take (suggestions, featured items, a shuffled gallery): the whole set, not only what this take
   showed.
2. Look at each sheet (`takes/review/01.jpg` and on) at full size. You may look too, but the person decides. Show
   them the sheets.
3. For any that fail: `reshoot check --review takes/review --fail 3-2 7-1`. It lists where each came from. Take those
   out of the demo data, then record the take again, since the take still shows them.
4. When the rest pass: `reshoot check --review takes/review --ok`. Passed images are remembered by a hash of their
   bytes, so the next round shows only what's new.
5. Repeat until `reshoot check` says everything has been checked.

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
- An automatic check (faces, names) helps find problems, but it doesn't replace looking.
