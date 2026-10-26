# Narrated web app workshop

This implements the [video plan](../plans/2026-10-26-tutorial-video.md).
The [source recipe](../../examples/tutorial/README.md) and
[written companion](../../guide/video-workshop.md) teach one synthetic notes
task from URL-based demonstration through editing, repair and final download.
The native runs and workshop remain pending owner review.

## What is recorded

The workshop uses the real recorder and Studio with native automated browser
input. The filming hook supplies that hand in a fresh headless browser;
business actions, result checks, edits, failed recordings and repairs are not
mocked. Each capture is of a browser page, never the desktop. The notes fixture
is the only app/data source. Local synthetic narration uses the installed
Samantha voice and is disclosed in the lesson and review player.

The lesson has 41 scenes in nine chapters. The opening plays the completed
native demo, holding its result under the introduction. The main workflow
demonstrates URL-based creation, explicit result checks, preview playback,
captions, holds, Undo/Redo, export framing, a separately reviewed replacement
action, styling, narration, an opening card, an actual broken target and
repair, paired comparison, readable recording size, final review and download.

Command graphics are instructions rather than invented terminal output.
The initial preview-generation wait is omitted and labeled. Later wait edits
remove only time inside recorded generation waits; typing/clicking retain
their speed. The edit map records retained source ranges, detail crops and the
opening result hold. Raw page footage, speech, before-change sources, native
run reports and all failed filming attempts are retained locally.

## Production checks

- The complete fast suite passed with 332 tests. Focused checks cover wait
  boundaries, caption rounding, long QuickTime chapters with subtitles/audio,
  bounded HTTP seek ranges, protection against outside-root symlinks, and the
  documentation constraints.
- A browser regression records a synthetic bottom-edge control and confirms
  it remains visible and changes color in the encoded 1440 by 810 page video.
- A fast real-workflow rehearsal exercised creation through repair, comparison,
  final review and downloading, without accepting media. The full narrated
  capture adds the measured compact-view refinement.
- Python 3.11 syntax and local documentation links/anchors were checked.

Filming exposed Chrome's headless screencast using only 723 pixels of an
810-pixel emulated page. The corrected recipe explicitly sets the window and
scale, captures a real initial frame for static scenes, and rejects clipped
stream dimensions. A clean retake replaces the affected footage. The earlier
attempts stay available for diagnosis.

FFmpeg 9.0.2's automatic movie timescale truncated long QuickTime chapter
packets even when the alternative chapter metadata appeared complete. The
recipe sets a 1000-tick movie timescale, and the audit checks the chapter track
itself against the full duration. The long-chapter regression reproduces this
case without needing a long, complex video fixture.

The small export also exposed a practical readability issue. The lesson now
switches from the wide view to a compact 640 by 480 recording and inspects a
fresh Fit export at 640 pixels viewing width. Readability hints remain advice;
the lesson does not claim that every text sample passes a universal threshold.

## Local candidate

The clean candidate is under ignored `takes/tutorial/attempt-daec9964bd55/`.

| File | Verified result |
|---|---|
| `exports/tutorial.mp4` | 15:10.55, 1920 by 1080, 30.99 MB, nine chapters, 214 caption cues |
| `exports/first-demo.mp4` | 2:28.02, 1920 by 1080, 4.26 MB, two chapters, 38 caption cues |
| `exports/*.srt`, `*.vtt` | Separate captions, also embedded in each MP4 |
| `exports/transcript.md` | Chaptered narration with command graphics in text |
| `review/index.html` | Chapter player, transcripts, scan links and encoded-frame contact sheets |
| `exports/notes-demo-exports.zip` | Downloaded through Studio; every file hash matches the displayed native final |

The audit passed. Audio/video duration differs by about 21 milliseconds in
each edit. Narration mean level is -17.6 dBFS; peaks are -2.3 dBFS and -2.7
dBFS, without clipping. Chapter-track duration, cue order and boundaries,
all scene frames and the downloaded archive were checked. Encoded-frame samples
for all 41 scenes and key action frames were inspected by the maintainer.

The final native run is `f9026f4f219f4b2da2ed2d8e12e3fbab`, with both original
result checks passing. The complete capture retains seven successful native
runs and the intended failed refresh. Every native recording remains pending
review; no acceptance controls were used.

The Vision scan completed with zero findings and no errors across 354 sampled
video frames and two exact subtitle files. It sampled every three seconds;
229 distinct unchecked items remain for human review after duplicate handling.
This is not an every-frame scan or owner approval.

The local player was checked at 1600 px and 390 px widths: nine chapter
controls, successful seeking, 214 loaded caption cues, no page errors and no
horizontal overflow. A range-aware loopback server supports browser seeking;
Python's basic server could stall on later chapters. The source includes the
tested server and its `build.py serve` command.

The companion's fixture initialization and local-server steps were executed
against a fresh synthetic project. Python 3.11 syntax and documentation links
were rechecked. No accepted media in `docs/demo/` was replaced; the audit
verified its original hashes. Nothing was pushed, posted or published.

Owner watch-through and acceptance, and independent learner testing, remain
separate from these implementation and maintainer-operated checks.
