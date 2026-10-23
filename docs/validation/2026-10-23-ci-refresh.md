# CI refresh trial

On 2026-10-23 the refresh loop ran end to end on GitHub's Ubuntu runners in a
private throwaway repository, `mumit/reshoot-ci-trial`. Its app is the bundled
notes example with made-up data, in `demo/`. The workflow used the reshoot
working tree under test, vendored into the repository as `.reshoot/`, so nothing
unreleased was pushed to reshoot itself.

## What ran

| Run | Trigger | Change | Result |
|---|---|---|---|
| 40024822242 | manual | none; the shipped `candidate.yml` | Recorded; checks passed; artifact only |
| 40026194932 | manual | none; `refresh.yml`, no `demo/accepted/` yet | Recorded; PR #1 without a comparison |
| 40026434810 | push | heading "My notes", blue accent | Recorded; PR #2 compared with PR #1's record |
| 40026663420 | push | search input renamed from `q` to `note-search` | Failed on beat `search`; no PR |
| 40027090240 | manual | the same, after clearer failure messages | Failed on beat `search`, naming the target; no PR |
| 40027248765 | push | story target repaired to `#note-search` | Recorded; PR #3 compared with PR #2's record |

PR #1 and PR #2 were merged, which in this workflow accepts the recording.
Merging did not start another run: the `!demo/accepted/**` path filter held.
PR #3 was left open.

## What it shows

- The shipped candidate workflow records on Ubuntu: 1280 by 720, 7.6 seconds,
  three passed checks, a completed scan with nothing flagged. Linux fonts render
  the notes app cleanly.
- The refresh workflow bootstraps: with no record, it opens a pull request with
  the media and the first `demo/accepted/` record.
- A visible change that keeps the story working produces a pull request whose
  GIF shows the change. The GIF fetched from PR #2's branch shows "My notes"
  and the blue accent. Its table matched all four beats with unchanged
  definitions and results.
- A breaking change fails on the beat it breaks and opens no pull request. The
  artifact keeps the run, its report and a failure screenshot.
- A story repair produces a pull request whose table marks only the `search`
  beat's definition as changed.

## Changes made during the trial

- The first breaking run reported only `action target must match exactly one
  element`, and the run's error named only the failed step. Both now name the
  beat and the target: `beat 'search' failed: type target {css = '#q'} matched
  0 elements; it must match exactly one`. Runs in GitHub Actions also write a
  job summary.
- The pull request body embeds the new GIF from the pull request's branch, so a
  reviewer sees it without downloading the artifact.
- The beat table's evidence column is labeled "Frame pixels". In every run the
  evidence frames of unchanged beats differed slightly, from the cursor and
  timing, so that column is not a change signal by itself.

## Limits

- One repository, one app, one maintainer acting as owner. No outside reviewer
  used the pull requests.
- The scan in CI uses Tesseract for text only; faces and people were not checked.
- Reviewing still needs the artifact's `review.html` for the MP4 and the scan
  sheets; the pull request shows only the GIF and the table.
- Records merged from CI carry `review_status` pending: the merge is the
  acceptance, and it is not bound to artifact hashes the way `reshoot accept` is.
