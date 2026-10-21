# Positive face and person detection fixtures

Recorded on October 20, 2026, Vancouver time (October 21 UTC).

Status: all three technical fixture expectations passed on this Mac. Vision
flagged a clear portrait face and a standing person's face and body, and left a
deterministic no-person control unflagged. The generated images, prompts, original
failed attempt, successful attempt and contact sheet are retained locally.

## Fixtures and expectations

The built-in imagegen tool created two fictional adults without reference photos.
The first prompt requests an unobstructed, front-facing head-and-shoulders
portrait against a plain gray background. The second requests an upright adult,
with the entire body and both feet visible against a plain gray background.
Both source images were inspected and copied unchanged into the workspace. A
third fixture draws a rectangular panel and three rectangular bars locally;
it contains no person or text. No real photo, account or personal file was used.

The checks were specified before scanning: the portrait must have a face flag,
the standing figure must have a person flag, and the control must have neither.
The runner also requires finite, positive boxes within the image bounds. The
portrait box must contain the image centre; the standing-person box must contain
the central torso and span at least half the image height.

| Fixture | Dimensions | Direct Vision findings | Expected result |
|---|---|---|---|
| Portrait | 1254 by 1254 | Face, 85% confidence | Passed |
| Standing figure | 1024 by 1536 | Face, 88%; person, 84% | Passed |
| No-person control | 1024 by 1024 | No findings | Passed |

These are the detector's reported confidence values, not measured accuracy.
The portrait's optional person detection was absent; the required face detection
passed. The standing figure's person box covers approximately 84% of the image
height, including head and feet.

## Actual scanner and CLI

The runner calls the unchanged public `reshoot.scan.scan(image, engine='vision')`
on each original fixture. It then runs the actual `reshoot check` command on the
same three files with explicit `--ocr vision` and a fresh review directory.

The CLI completed text and people detection using Vision on macOS 27.0.1 arm64,
with reshoot rules version 0.2.0. It flagged the two positive images with the same
face/person reasons and left the control unflagged. The report has three samples,
two flagged items and zero detector errors. Its exit 1 means the independent
human-review checklist is pending; the expected positive flags are test successes.
These supplied still images are scanned directly, without video-frame sampling,
although the generic report labels its default mode `sampled`.

The exact contact sheet was inspected: the portrait box encloses the face; the
standing figure has a face box and a full-body box; the control has no box.
An audit verified all three original fixture hashes, the prompts and fixture
receipt, seven generated review-file hashes, and correct contact-sheet item
mapping. The scanner's retained originals have identical decoded pixels to all
three inputs, even where PNG container bytes differ.

## Retained environment failure

The first sandboxed attempt failed after 0.412 seconds with
`Vision failed (unknown unknown)`, before producing findings. It remains under
`attempt-6efcf1b021ae/`. An approved rerun outside the sandbox used the same files,
prompts, backend and runner, and passed in 1.983 seconds under
`attempt-88cdaccf0392/`. There was no detector fallback or replacement fixture.
This establishes successful operation outside that sandbox; the sandboxed Vision
failure remains a compatibility limitation.

## Scope and local evidence

This is a positive compatibility check using two generated images and one simple
control on one host. It does not measure recall, false-positive rates, demographic
coverage, small or obscured faces, crowds, unusual poses, other image formats or
other platforms. The positive fixtures are deliberately flagged and have no demo
image approval. No human checklist has been marked accepted. No implementation
code, commit, push or publication was involved.

Evidence is under ignored `takes/compatibility-20261020/positive-detection/`:

- `PLAN.md` and `prompts.json`: initial expectations and exact built-in prompts.
- `fixtures/portrait.png` and `fixtures/person.png`: generated originals, copied
  into the workspace without edits.
- `fixtures/no-person.png` and `fixture-receipt.json`: deterministic control,
  image dimensions, hashes and provenance.
- `run.py`: direct scanner and real CLI checks, preserving each attempt.
- Both `attempt-*/result.json` files: failed and successful observations.
- `attempt-88cdaccf0392/review/01.jpg`: exact inspected contact sheet, with its
  report, flags, key and retained original images beside it.
- `results.json` and `index.html`: verified technical summary and local viewer.
