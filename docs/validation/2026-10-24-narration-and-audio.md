# Narration auditioning and audio balance

On 2026-10-24 the local macOS checkout exercised the narration and audio
milestone in the [creation and revision plan](../../UX_PLAN.md). Tests and
agent-operated trials used only synthetic notes data, generated tones and
local system speech. This is not independent-user research or owner acceptance.

## What changed

Each story step has optional spoken words with Save, Reset and a saved-line
audition. A separate Audio panel offers voices listed by the local speech
tool, a project music track, narration/music levels and optional ducking.
Narration and audio operations share validated CLI/studio file edits,
project revision guards and session Undo/Redo. Custom project speech commands
remain file/CLI settings, rather than arbitrary commands accepted from the page.

Auditions prepare one line using the recording's cache, with project-relative
commands resolved from the same directory. They do not start the app or create
a new video run. The studio guards the saved-line cache key when starting the
command, permits cancellation and retains the displayed successful video on
failure. Narration changes are identified beside the step; Update preview
records the whole task again so its beats can wait for the new speech.

Balance changes re-cut a current recording. Linear narration gain is 0 to 2,
music gain 0 to 1; the studio displays percentages. Ducking lowers music while
the voice speaks, and music retains its ending fade. Muting narration preserves
its beat timing and subtitles. A final limiter leaves headroom before AAC
encoding, with latency compensation. This is not loudness normalization.

## Fresh CLI trial

The ignored `takes/audio-20261024/` directory contains `trial.py`, `trial.json`
and the command logs. The documented narration commands were run against a
new packaged notes project, with a generated music track and macOS's default
voice. An additional `say -v Samantha` audition succeeded, then the project's
voice returned to the default.

| Stage | Evidence |
|---|---|
| Audition the search line | 1.34 seconds elapsed; a 1.45-second WAV |
| Record two narrated steps | Run `02e192a620034cb0a24f80b500d1d705`; 18.65 seconds; all 3 checks passed |
| Set narration to 60% and music to 8%, then re-cut | Run `27e65a4f23e54725897d037c4af0e754`; 4.94 seconds; all 3 original checks retained |

The intro line lasted 2.07 seconds. Both spoken lines appeared in the rendered
subtitles. The balance re-cut retained the storyboard bytes and the clean take's
SHA-256: `a780b85e513ed6e65775727e5b683cb6c6d1545b3a593cff97c2ab76a9f5f923`.
Privacy scanning was disabled for this audio/timing trial; run sheets and text
scan items do not establish a privacy scan pass. No media was accepted or
published.

## Verification

The broader browser suite passed all three affected audio, studio and framing
journeys. The final enhanced audio journey also passed, adding narration-change
indicators, a failed engine and cancellation. It verifies pending-field
protection, saved-line audition playback, Undo/Redo, retention of the displayed
run, a fresh capture after narration edits and a balance re-cut that keeps the
clean recording, subtitles and three result checks.

Encoded-tone tests measure the music frequency with and without ducking,
halved narration amplitude, muted music/voice, voice onset timing and a limited
peak after AAC encoding. File tests cover invalid settings without partial
writes, quoted/inline TOML, preserved comments, project-relative speech commands,
cache reuse, stale auditions and stale edits. Existing timing and narration
regressions also pass.

| Check | Result |
|---|---|
| Complete fast suite | 176 passed, 46 browser tests deselected |
| Affected audio, studio and framing browser suite | 3 passed |
| Final enhanced audio browser journey | 1 passed |
| Documentation | Relative links, images and anchors checked; 22 TOML blocks parsed, including separate target alternatives |
| Static and package checks | Python compilation, studio JavaScript syntax and whitespace checks passed; wheel includes audio operations and updated skills |
| Plugin | Validation passed with existing context-file and missing-icon warnings |

The local studio's narration and Audio panels were visually inspected beside
the fresh notes video. The notes gallery was rebuilt and its caption, framing
and style images inspected.

## Limits and following work

This trial does not grade voice naturalness, music choice, intelligibility or
professional creative quality. Native voices differ by OS and installation;
discovery failure retains the system-default and configured project choices.
No Linux speech or outside-user trial was added. Custom speech tools can use a
service, but these trials used local tools only.

Auditions are dry voice samples outside the run's media review. The owner must
listen to the finished MP4 and review its subtitles; GIFs remain silent. AAC can
slightly overshoot the pre-encoding peak ceiling. Mute retains narration timing;
removing its line and recording again removes that hold. The studio and CLI
edit the first TOML browser take; other takes remain file-editable. Undo lasts
for the studio session. Screenshots for docs are the next milestone.
