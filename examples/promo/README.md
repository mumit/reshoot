# A demo that stays current

This is reshoot's promotional recording recipe. The small notes app changes its
heading, button label and appearance; the same native storyboard saves and finds
the same synthetic note in both versions. The original `examples/notes/` tutorial
and `docs/demo/notes.*` are preserved.

Run from the repository root in an environment with reshoot's browser extra and
Pillow installed. Install Chrome/Chromium, ffmpeg and VHS first. On macOS:

```bash
brew install ffmpeg vhs
uv sync --extra browser
uv run python examples/promo/build.py
```

The script starts only its own loopback server, records browser pages and a clean
VHS terminal, and retains every attempt under ignored `takes/promo/attempt-ID/`.
It records a preview and a fresh final for each app version. The updated final
runs through the actual command typed in VHS:

```bash
reshoot run examples/promo/release-v2.toml
```

The terminal uses a wrapper that captures raw CLI logs off-screen and prints a
short summary derived from the resulting native run report. This prevents host
paths and environment details appearing in the video. The complete terminal
take, raw logs, wrapper and tape are retained. The social edit removes generation
waiting and labels that omission; it makes no generation-time claim. The app task
plays at its original speed. The authored promotion is an edited video.

Outputs are `exports/reshoot-social.mp4` (4:5), `reshoot-readme.gif` and its MP4
companion. `review/index.html` presents them with links to native-result evidence,
actual encoded frames and the uncut terminal capture. Generated files do not
replace the README media or become approved automatically.

To repeat only an edit or its media audit, select an exact retained attempt:

```bash
uv run python examples/promo/build.py compose --attempt takes/promo/attempt-ID
uv run python examples/promo/build.py audit --attempt takes/promo/attempt-ID
```

Review final exports and run `reshoot check ... --full` on the social MP4 and
README GIF, with exact subtitle text where applicable. Read the reported backend
and coverage. Owner recording acceptance and human scan-sheet approval are
separate. Do not publish or overwrite approved artifacts without an explicit
decision. The runner never commits, pushes or posts.

This recipe targets macOS and Linux shells. A different-machine reproduction is
still required; it is not evidence for novice use when the existing maintainer
operates that machine.
