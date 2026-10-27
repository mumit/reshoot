# Workshop with Kokoro Heart

The owner selected Heart from the local Kokoro auditions. The workshop and
first-demo excerpt were rebuilt with `kokoro --voice af_heart --speed 1`.
Voice selection is approved; review of the complete new edits remains pending.

## Rebuild

```bash
uv sync --extra browser --extra kokoro
uv run python examples/tutorial/build.py renarrate --attempt takes/tutorial/attempt-daec9964bd55
```

This produced `takes/tutorial/attempt-8e8e4eff040e/`. All 41 narration passages
were synthesized locally using downloaded model files with `HF_HUB_OFFLINE=1`.
The edition preserves the original footage and native demo evidence. A file
comparison verified 397 copied files and the downloaded demo bundle against
the original. Original recordings and accepted repository media are unchanged.

The lesson now distinguishes its Heart narration from the original voice in
the demonstrated demo downloads. The player identifies Heart explicitly.
No human narration import or paid service was added.

## Audio and media

The initial Heart export measured -26.81 LUFS. Both edits now use two-pass
loudness normalization targeting -18 LUFS and a -2 dB true-peak limit. The
recipe saves its measurements beside each export. This changes audio level
without changing the scene cuts or caption times.

| Export | Duration | Size | Chapters | Cues | Measured LUFS | True peak |
|---|---|---|---|---|---|---|
| Workshop | 919.500 s | 30,968,842 bytes | 9 | 237 | -18.02 | -1.94 dB |
| First demo | 151.200 s | 4,336,210 bytes | 2 | 40 | -18.05 | -1.98 dB |

Both exports are 1920 by 1080 with audio and embedded subtitles. Audio/video
duration differences are 100 ms and 33 ms respectively. Chapter tracks cover
the edits, and caption cues are ordered and remain within their media.
Encoded opening and closing contact sheets were visually inspected.

## Verification

- Twenty targeted tutorial, Kokoro and documentation tests passed, including
  preservation of the original capture, rejection of changed scene order,
  normalization of a quiet encoded audio fixture, and long chapter retention.
- The final media audit passed. Its privacy scan sampled 358 frames, checked
  two exact subtitle files and reported zero findings across 228 distinct
  images. This is sampled coverage, not inspection of every frame.
- The original final native run still has its two passing result checks;
  its media and downloaded bundle match their recorded hashes.
- The localhost player has 82 working asset links. Both normalized MP4s
  support byte-range seeking. A local server serves this edition at its own
  review URL.
- `git diff --check` passed.

The audit, scan, word timings, source snapshots, copied-capture comparison and
normalization measurements remain under the new ignored attempt directory.
No acceptance was recorded, and nothing was pushed or published.
