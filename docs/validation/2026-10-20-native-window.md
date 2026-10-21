# Native macOS window recording trial

Recorded on October 20, 2026, Vancouver time (October 21 UTC).

Status: the native window capture, export, encoded-content checks, sampled scan
and cleanup passed on this Mac. The owner accepted the exact 10.10-second MP4
after confirming that its instant text update is intentional. The separate
scan-sheet checklist remains pending.

## Fixture and capture scope

A disposable Python/AppKit app creates one native macOS window titled
“Reshoot Synthetic Notes Trial.” It shows two made-up notes, a “Save demo note”
button and a status label. Four seconds after the recording signal, an internal
timer presses that button, adding “Pick up the bikes” and showing the saved-note
status. This checks capture of a native UI update; it does not test operating
system mouse or keyboard automation. The handler redraws the whole text area;
existing notes move down immediately when the new note is inserted. The owner
asked about that instant appearance around four seconds and accepted it on the
condition that it was intentional, which the fixture source confirms.

The runner verifies that the window is on screen and that its owner PID matches
the fixture subprocess. It then calls the actual CLI with explicit `--id 23641`
and `-s 10`. `reshoot window` uses `screencapture -x -v -V10 -l23641` for that
selected window. There is no whole-screen capture, existing document, real
account, photo or other app data in the fixture. Only the selected window's
metadata is retained.

The selected native window was 820 by 568 points, including its title bar. The
saved opaque window area is exactly 1640 by 1136 pixels, matching 2x scaling.
Its surrounding shadow and black background bring the recording to 1864 by
1360 pixels. Opening, middle and ending encoded frames were inspected, including
the title bar, corners, note list and status. Only the synthetic window and its
surrounding capture background are visible in those frames.

The host reports macOS 27.0.1 arm64. A sandboxed readiness query reported Screen
Recording access unavailable. In the approved outside-sandbox runner, preflight
was true before and after capture, and the actual capture succeeded on its first
attempt. No system permission setting was changed.

## Results

| Measurement | Result |
|---|---:|
| Original MOV duration | 10.101667 s |
| MP4 export duration | 10.100000 s |
| Raw and exported dimensions | 1864 by 1360 |
| Raw and exported encoded frames | 362 each |
| MP4 average frame rate | 3620/101, approximately 35.84 fps |
| MOV size | 403,888 bytes |
| MP4 size | 183,095 bytes |
| Runner elapsed time | 17.327 s |
| Sampled Vision scan | 11 frames, zero flags/errors |
| Fixture exit code | 0 |
| Owned windows remaining | 0 |

The raw and exported files are H.264. The MP4 uses yuv420p, contains no audio,
and retains the entire take and its original frame count. Its frame timing is
variable; this is not a 60 fps browser export. Both files decoded fully without
reported errors.

Independent Tesseract OCR on three extracted MP4 frames verifies that the opening
contains the original notes and no “Pick up the bikes.” The middle and final
frames contain both that note and “Saved demo note: Pick up the bikes,” while
retaining an original note and the exact synthetic window title. The fixture log
also records the save action, but encoded-frame checks establish the visible
result independently of that log. All five recorded media/frame hashes match,
and the fixture source hash is unchanged.

Vision completed text and people detection with explicit `--ocr vision` and
one-second frame sampling. Its report has eleven items on three sheets, no flags
and no detector errors. Exit 1 denotes the pending human image checklist. The
raw MOV was decoded and inspected; the automatic privacy check covers the MP4
samples. Unsampled frames are not covered by that scan.

The runner closes only its own fixture, waits for its process to exit and checks
that the fixture has no remaining on-screen windows. The saved recordings and
evidence remain available for review.

## Limits and review

This validates one disposable AppKit window on one Mac. It does not establish
compatibility with other desktop apps, display arrangements, obscured or minimized
windows, changing window IDs during a take, longer captures or other platforms.
It adds no native storyboard assertions or input automation to the CLI.

The local review page contains the exact MP4, original MOV, three encoded frames
and links to the scan sheets. Owner recording acceptance is separate from the
scan-sheet checklist. An exact artifact-bound acceptance receipt records the
owner's conditional verdict and the satisfied condition. This standalone window
CLI take has no native project review manifest; acceptance is saved in its local
receipt and technical summary. No implementation code, commit, push or
publication was involved.

## Local evidence

Evidence is under ignored `takes/compatibility-20261020/native-window/`:

- `fixture.py`: disposable native notes app using made-up data.
- `run.py`: verifies window ownership, records by ID, exports, scans and cleans up.
- `attempt-7a7eb23cf5b2/`: capture command and logs, ownership receipt, source MOV,
  MP4, extracted frames, OCR text, fixture events and scan sheets.
- `audit.py` and `results.json`: media hashes, decoding, geometry, encoded-text
  checks and cleanup results.
- `index.html` and `presentation.json`: local review page and exact MP4/MOV hashes.
- `acceptance.json`: exact owner verdict, intentional-update condition and
  accepted artifact hashes.

MP4 SHA-256:
`c54e96bc5a36dc27407257a3731e6616cdac3297b50230e6fc2df2a782e2aa54`.
