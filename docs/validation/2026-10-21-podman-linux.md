# Linux compatibility trial in Podman

Status: the owner ran the Linux instructions and reported: “All tests passed on
linux, and the final mp4 and gifs look good.” The copied logs show two separate
test runs: regular tests, 68 passed and 26 deselected; browser tests, 26 passed and
68 deselected. There is no single run reporting “94 passed.” The packaged notes
preview and fresh final passed their task assertions,
encoding and sampled text scanning. The owner's positive visual review is recorded
against the exact final MP4 and GIF hashes. The initial packaged trial changed no
implementation; the subsequent promo-recipe repair is documented below.

## Environment and source

The trial used a Debian GNU/Linux 12 (Bookworm) container in Podman's Linux VM on
the existing Mac. Copied environment files report:

- Linux `7.2.5-200.fc44.aarch64`, ARM64.
- Python 3.11.2, pytest 9.1.1, Playwright 1.58.0.
- Chromium 155.0.8059.79 for Debian 12.
- Tesseract 5.3.0, text scanning only; face/person detection unavailable.
- reshoot 0.2.0 installed from `/work/src` into a Python virtual environment.

The supplied source archive is byte-identical to `git archive --format=tar` of
commit `47e50d7520b97fb3ce87cdeb3be2035714e25d52`. The packaged project was created
and exercised at `/work/linux-demo`, outside the source checkout. The instructions
are saved locally in `takes/podman-linux-test.md`. The initial evidence did not
include container inspection; it was retained during the subsequent promo trial.

## Verified results

| Check | Result |
|---|---|
| Regular tests | 68 passed, 26 deselected; 11.36 s |
| Browser tests | 26 passed, 68 deselected; 174.57 s |
| Dependency doctor | ffmpeg, ffprobe, Chromium and Playwright available |
| Preview | `6f30a889cf8345bfb7725a396ca6a046`; 3 assertions passed; 13 s reported execution |
| Fresh final | `0d04d2a47ece45e79bbf71312664b87c`; 3 assertions passed; 14 s reported execution |
| Native manifest verification | 32 file hashes verified across both runs |
| Final MP4 | 7.433333 s; 1280 by 720; 446 frames; 200,643 bytes |
| Final README GIF | 7.47 s; 800 by 450; 112 frames; 325,268 bytes |
| Sampled scans | Both completed; 6 samples and 2 subtitle files per run; zero flags/errors |

All four preview/final MP4 and GIF exports were fully decoded during the local
audit without reported errors. Six native assertions passed across the two runs.
The task saves “Pick up the bikes” and searches for “bike.” Execution timings are
reported command durations, not setup, owner-review time or a speed comparison.

Final MP4 SHA-256:
`86ecce9a8fdc00e4f766689b0887301686ab43579af6b58f6b6658b51805a02f`.

Final GIF SHA-256:
`2a5be322807d9cbcf9d57d815604cf39227de743cda1c82db7fac4852518cb1b`.

## Review and limits

The owner's positive visual verdict covers the final exports. The copied native
run reports and scan checklists retain their original pending review states;
no raw-take decisions or scan-sheet approvals were inferred or imported. Each
scan samples every three seconds and leaves six items on two sheets. There is no
full-frame privacy scan or Linux face/person detector in this trial.

This establishes the tested packaged browser workflow in a fresh Linux ARM64
container on this Mac. It is not a separate physical-machine or novice-user
trial. Other Linux architectures, native desktop capture and broader workloads
remain separate. The full promotional recipe was subsequently exercised below.
The accepted macOS promotion and its approved scan sets remain unchanged.

## Full promotional build and repair

The owner followed `takes/podman-linux-promo-test.md` in the existing container,
adding VHS 0.12.1 and ttyd 1.7.7. A standalone VHS probe completed and decoded.
Debian ffmpeg is 5.1.9. Attempt `f462dd8857fd` recorded all four native runs and
composed the exports, then failed the exact H.264/30 fps audit. The social MP4's
average frame rate was `3333120/111109`, despite every input clip being exactly
30 fps. Timestamp inspection found two irregular joins, accumulating 15 ticks
at a 1/15360-second time base, about one millisecond. Stream-copy concatenation
had used rounded container durations.

The original failed attempt was copied back before changes and backed up inside
the container under `/work/promo-results-01/failure-01/`. The promo composition
now decodes and joins its clips with timestamps derived from frame count at
30 fps. The audit's exact frame-rate requirement remains intact. Separate MP4
and GIF review-image filenames prevent evidence overwrites, and build errors
include the failing step's stderr tail. These are promo-recipe changes; the
installed reshoot engine and native recordings were not changed.

Only composition and audit were rerun. Both passed on Linux. Independent checks
of the copied evidence verified 36 native manifest hashes, 24 passed assertions,
four matched beat definitions, all 12 distinct export review-frame hashes and
the presentation bindings. The terminal summary passed OCR and was inspected.
All three exports fully decode. Every MP4 frame interval is exactly 1/30 second,
and each export retains its original frame count. All 115 native evidence and
captured-recipe files match their pre-repair hashes.

| Repaired export | Duration | Dimensions | Frames |
|---|---|---|---|
| Social MP4 | 21.70 s | 1080 by 1350 | 651 |
| README MP4 | 9.167 s | 1200 by 800 | 275 |
| README GIF | 9.16 s | 960 by 640 | 110 |

The owner accepted all three repaired exports with “Accepted.” Local
`acceptance.json` binds the exact verdict to the presented export hashes, and
`acceptance-audit.json` verifies them. The presented results, page and verification
record are preserved under `acceptance-evidence/`; the original presentation is
unchanged. The local results and review page now show export acceptance. The
container's original technical audit record remains unchanged. The owner also
completed the separate privacy scan-sheet review described below; no native
source-run decisions were imported.
Accepted macOS media hashes remain unchanged. Do not rerun composition or audit
over this accepted attempt.

The owner then asked how to complete scan-sheet review. Fresh full-frame scans
of all three accepted Linux-generated exports were prepared on the Mac with
Vision, including exact SRT text. All 1,036 decoded frames are covered by 830
distinct images on 208 sheets: social MP4 119, README MP4 63, README GIF 26.
The automatic scans completed with zero flags/errors. Original image pixels and
decoded-frame identities were verified; accepted export evidence is unchanged.
The viewer at `repaired/attempt-f462dd8857fd/review/scan-sheets.html` under the
promo evidence folder provides numbered sheets and links to full-size originals.
`scan-review.json` records export hashes, policies and hashes of all review files.
The owner approved all three sets with “Reviewed all three Linux promo scan sets;
approved”. The actual CLI `check --ok` completed for all three review directories;
their reports now show review completed. `scan-acceptance.json` and
`scan-acceptance-audit.json` bind the exact verdict to 208 sheets, 830 images,
1,036 frames and the scan policies. All checked entries match their policies;
sheet, key, flag, original-image and accepted-media hashes are unchanged.
`scan-approval-evidence/` preserves the pre-approval reports, results and pages.
No review remains open for these three promo exports or scan sets. Earlier
packaged notes and native source-run checklists remain unchanged.
Initial sandbox Vision failures are retained in
separate `*-vision-error` directories/logs; retries outside the sandbox completed.
This is macOS scanning of Linux artifacts, not Linux face/person detection.

## Local evidence

Ignored evidence is under `takes/podman-linux-47e50d7/`:

- `source.tar`: exact committed source archive.
- `results/`: installation, doctor, test, preview and final logs, plus copied
  distribution, kernel, browser and Python package versions.
- `linux-demo/`: packaged synthetic project and both original run directories,
  native reports, task evidence, exported media and scan sheets.
- `audit.py` and `results.json`: source-archive comparison, manifest verification,
  assertion totals, full media decoding, export metadata and log hashes.
- `owner-report.json`: exact owner message, final run binding and export hashes;
  it does not approve scan sheets or authorize publication.

The full promotion's evidence is separately retained in
`takes/podman-promo-47e50d7/`: `promo/` preserves the failed attempt,
`native-project/` contains all four original native runs, `setup-and-build/`
contains installation/probe/build logs, and `container-inspect.json` records the
container. `repaired/attempt-f462dd8857fd/` holds the repaired exports and review
page. `repair-evidence/recovery.json` binds the recipe repair and before/after
raw hashes; `verify-repair.py` and `repair-verification.json` record the independent
copy verification and final export hashes.

After completing export and scan-sheet reviews, the owner authorized two local
checkpoint commits: the promo repair (`7989c5d`) and these validation records.
Nothing has been pushed or published.
