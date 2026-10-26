# Local Kokoro narration audition

The owner's feedback rejected the workshop's macOS system narration. This
change adds optional local Kokoro English speech and a short comparison before
another full workshop render. No human narration import was added.

## Implementation

- Install with `reshoot[browser,kokoro]`, or `uv sync --extra browser --extra kokoro`.
- `voice_engine = "kokoro --voice af_heart --speed 1"` uses a lazy, CPU-only
  pipeline. The normal CLI needs no neural speech packages. First use downloads
  model weights, the voice pack and English language data.
- The CLI audition, Studio and recorder share the existing narration cache.
  Voice and speed changes produce different cache keys. Four English choices
  appear in Studio when the extra is installed.
- Workshop speech uses connected passages and Kokoro word timestamps, including
  offsets across model chunks. Caption grouping retains trailing punctuation.
- `examples/tutorial/audition.py` renders the same shorter spoken script and
  original notes footage with Heart, Bella and Michael. The workshop recipe
  now selects Heart as its initial candidate; no full workshop was regenerated.

## Evidence

The final comparison is under ignored
`takes/kokoro-audition-89f86c294927/`. Each MP4 is 41.254 seconds, has nine
caption cues, audio, video and subtitles, and is approximately 1.1 MB.
All three decode fully, cues are ordered and within the media duration, and
the comparison page's 12 media/transcript links load. A contact sheet was
visually inspected. Listening review and voice selection remain pending.

The three samples were regenerated with `HF_HUB_OFFLINE=1` using downloaded
model files. This verified local synthesis without a model Hub connection.

A fresh synthetic notes project at `takes/kokoro-native-smoke/` used Heart
narration in an actual headless Chrome preview. Run
`d373d0a013894389b8185da137752314` completed in 18 seconds, passed all three
result checks, exported MP4 and GIF, and scanned eight items with zero flags.
The narrated beat reused its audition WAV. The run remains unaccepted.

## Checks

- All 341 fast tests verified: 340 passed in the full run, and the remaining
  test passed after correcting its exact floating-point assertion to use a
  tolerance. No production change was needed for that assertion.
- The full suite initially encountered the expected sandbox restrictions on
  localhost sockets and macOS Vision; it was rerun with those capabilities.
- Documentation checks passed after the final wording changes.
- `uv lock --check --offline` and `git diff --check` passed.
- `claude plugin validate .` passed with warnings about the existing root
  `CLAUDE.md` context and missing plugin icon.

Only synthetic notes data and existing headless page footage were used. The
downloaded weights and generated media stay under ignored `takes/`. Accepted
repository media was not replaced, and nothing was pushed or published.
