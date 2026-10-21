# Five-minute continuous-animation compatibility trial

Recorded on October 20, 2026, Vancouver time (October 21 UTC).

Status: technical checks passed on this Mac. The 309.33-second final contains a
five-minute continuous canvas animation alongside the synthetic notes example.
The owner accepted the exact recording with “I accept”; bound decisions are
imported and run review is completed. Separate scan-sheet review remains pending.
This extends the
[earlier mostly static two-minute trial](2026-10-20-resume-validation.md#longer-recording).

## Fixture and scope

An isolated copy of `examples/notes/index.html` adds a canvas with seven moving
circles, an elapsed-time counter, a progress bar and start/stop controls. Everything
is drawn locally; there are no photos, accounts or external services. The native
TOML storyboard adds “Pick up the bikes,” searches for “bike,” starts the animation,
holds for 300 seconds, stops it and verifies both completion and the retained
search result. Only the headless browser page is recorded.

The project uses 1280 by 720 at pixel ratio 1, dark theme, seed 1, en-US locale
and UTC browser time. The host reports macOS 27.0.1 on arm64, with Chrome
155.0.8059.85. The final is silent H.264 at 60 encoded frames per second. There is
one full MP4 export; no GIF, zoom, narration or manual video editing is involved.
The edit retains the entire take, including the end verification.

The protocol and hashes of all five project inputs were saved before recording.
The project ran once, successfully. The audit verified the protocol digest, input
hashes, all 13 manifest artifact hashes, raw-video hash, final encoding and seven
passed native expectations. No product implementation changed.

## Results

| Measurement | Result |
|---|---:|
| Final duration | 309.333333 s |
| Final encoded frames | 18,560 |
| Final size | 7,531,408 bytes |
| Captured browser frames | 18,188 |
| Verified animation hold | 300.031 s |
| Largest capture timestamp gap, whole take | 1.195 s |
| Project-reported elapsed time | 384.6 s |
| Capture and initial encoding step | 340.1 s |
| Edit step | 17.9 s |
| Measurement wrapper elapsed time | 386.526 s |
| Native result checks | 7 passed |
| Sampled Vision check | 31 samples, zero flags/errors |

The frame count and largest gap describe the whole take, including its initial
static beats. Captured paints differ from the 60 fps encoded output because the
encoder holds a browser frame until the next paint. A timestamp gap alone does
not establish dropped frames.

The final decoded without reported errors. For 298 seconds of its animation, a
728 by 95 pixel crop covers moving shapes and excludes the changing elapsed-time
text. All 298 one-second frame hashes differ from their neighbours. FFmpeg's
`freezedetect` found no freeze lasting one second at a `-45dB` threshold in that
interval. The same detector correctly flagged a 2.5-second held-frame control
made from an extracted encoded frame. This checks sustained visible movement;
it does not prove delivery of every browser paint or rule out shorter stalls.

Eight encoded frames were inspected across the opening, early, middle, late and
completed states. The animation timer reaches 300.5 seconds and the final status
reads “Five-minute animation completed,” with the matching note still visible.
A separate 12-second review video contains four seconds each from 10, 150 and
295 seconds. These excerpts and frame inspection do not constitute full playback.
Owner acceptance was recorded separately after presentation.

## Resource measurements

The wrapper sampled descendant-process resident memory and an owned temporary
directory approximately every two seconds, producing 181 samples. It also ran
the project under `/usr/bin/time -l`. The measurement wrapper itself is outside
the measured descendant tree.

| Measurement | Result |
|---|---:|
| Sampled peak sum of descendant RSS | 1,437,614,080 bytes (1,371 MiB) |
| `/usr/bin/time -l` maximum resident set size | 509,018,112 bytes (485 MiB) |
| Median descendant RSS, elapsed 30–60 s | 1,349.4 MiB |
| Median descendant RSS, elapsed 270–300 s | 1,190.2 MiB |
| Median combined Python RSS, elapsed 30–60 s | 101.6 MiB |
| Median combined Python RSS, elapsed 270–300 s | 102.1 MiB |
| Sampled capture spool peak | 929,138,329 bytes |
| Sampled encoding spool peak | 931,375,558 bytes |
| Sampled total temporary-file peak | 1,860,513,887 bytes (1.73 GiB) |
| Temporary files after completion | 0 bytes |

The two memory windows each contain 14 samples. Similar combined Python readings
and the absence of rising total RSS across these windows support this particular
five-minute run. They do not establish a memory bound for arbitrary durations.
The descendant sum includes Chrome helpers and may count shared pages more than
once. It differs from the process-accounting maximum; neither is total physical
system memory. Sampling can miss peaks. Temporary-file sizes count logical bytes,
not allocated disk blocks, and the capture and encoding copies overlap during
encoding.

## Review and limits

Vision 27.0.1 completed text and people detection on samples every ten seconds,
plus the generated subtitle sidecar. The report has zero flags or errors, with
31 items on eight sheets awaiting human review. This sampled policy does not
cover every frame. The owner accepted the exact hash-verified recording with
“I accept.” The video and all five story beats have bound accepted decisions;
run review is completed. This does not accept the separate scan sheets.
The local review page includes excerpts, the full recording,
encoded frames, and links to the native review bundle and scan sheets.

This is one duration, one synthetic workload and one host. Positive face/person
fixtures, changing remote services, other platforms, hour-long captures and
broader workload scaling remain open. Novice and other-user acceptance remain
separate work. Nothing was committed, pushed or published.

## Local evidence

All evidence is under ignored `takes/compatibility-20261020/`:

- `animated-notes.py`: fixture preparation and measured runner.
- `animation-protocol.json`: protocol and input hashes saved before recording.
- `attempt-23f2699077f4/`: command, host, stdout, stderr and resource samples.
- `animated-notes/takes/runs/699111174f9341c6bf2132868e0780ec/`: isolated run,
  source/final MP4s, manifest, native evidence and sampled scan sheets.
- `audit-animation.py` and `animation-results.json`: completed technical audit.
- `animation-presentation.json`, `animation-decisions.json` and
  `animation-acceptance.json`: exact presentation, bound decisions and owner verdict.
- `animation-review/index.html`: local owner review page, full video, excerpts,
  eight frames, motion hashes, freeze-check log and held-frame control log.

Final MP4 SHA-256:
`88c9c1c1c3634de7fdfdf053702a29b894d0c15e4fec705d28e8b32aefce9965`.
