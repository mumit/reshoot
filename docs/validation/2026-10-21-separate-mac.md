# Separate-Mac packaged workflow trial

Status: the owner reports following `takes/separate-machine-setup.md` fresh on a
separate Mac/account and accepts the final MP4/GIF visuals. Copied provenance,
native assertions, manifests and media decoding pass verification. Bound native
recording decisions are imported locally. The owner approved both final-export
privacy scan sets; their checklists report review completed. Skill discovery and
refresh on that machine have not been exercised.

## Environment and scope

- Owner-operated Apple Silicon Mac, 16 GB RAM (owner reported), macOS 27.0.1,
  build 26A434; command architecture `arm64`.
- Python 3.11.11, Playwright 1.58.0, Pillow 13.0.0, websockets 17.3,
  PyObjC 12.2.2, Chrome 155.0.8059.85, ffmpeg 9.0.2.
- Executed uv reports 0.6.13. Homebrew's prerequisite log separately reports
  uv 0.13.4 already installed; these are the recorded command outputs.
- Installed reshoot 0.2.0 Git provenance resolves to
  `898502277c1e57e872799682358b28e2d54c3e8e`.

This is separate-machine reproduction by the maintainer. It does not measure
novice use. The owner clarified: “I ran it fresh on a separate Mac, following the
setup instructions in separate-machine-setup.md”. The retained install command
says this exact reshoot revision was already installed, and prerequisites were
also already present. That log does not measure initial installation duration.
No rerun was requested. All 18 retained timed commands exited zero; their times
are command observations, not a complete setup-time or effort measurement.

## Verified recording and owner acceptance

| Check | Preview | Final |
|---|---|---|
| Run ID | `8b6d5d2cbd634397a2fe1d3c55614a96` | `4f83ba850e73435595b794f6b075e87b` |
| Execution | Passed; 12.5 s reported | Passed; 13.1 s reported |
| Expected results | 3 passed | 3 passed |
| Manifest files verified | 16 | 16 |
| Native sampled Vision scan | 6 samples, 2 text files; zero flags/errors | 6 samples, 2 text files; zero flags/errors |

All five generated project inputs match the packaged templates at the pinned
commit. All four preview/final exports decode without reported errors. The task
saves “Pick up the bikes” and finds the single matching note with “bike”.

Final exports:

| File | Duration | Dimensions | Frames | Bytes |
|---|---|---|---|---|
| MP4 | 7.40 s | 1280 by 720 | 444 | 191,336 |
| README GIF | 7.40 s | 800 by 450 | 111 | 293,929 |

MP4 SHA-256: `37f2c5fda3b7156e7f77b9c88b5015ff2d66f5e8e5d2e3349f05da36d964e013`.

GIF SHA-256: `0146ba4e1f3d5e9c809451fe4019aff973cdc699694f45c86abeac8f69baf6b9`.

The owner explicitly accepted the visuals and supplied `decisions.json`. Its
final run ID and artifact/policy binding match. The native CLI imported the
accepted video and four beat decisions into the copied final run, whose recording
review now reports completed. `acceptance.json` binds the owner's message and
supplied decisions to the final exports. Original reports and the original review
page are preserved under `acceptance-evidence/`. The native sampled privacy
checklists are unchanged and remain pending.

## Final privacy sheets

Fresh full-frame Vision scans of the accepted MP4 and GIF, including exact SRT
text, completed with zero flags/errors. Every decoded-frame identity and the saved
original image pixels were verified. All 555 frames are covered by 419 distinct
images on 106 sheets: MP4 84, GIF 22. The numbered viewer links every sheet and
full-size original. The owner approved both sets with “Reviewed both separate-Mac
scan sets; approved.” The CLI applied `check --ok` to both full-frame review
directories. All checked entries match the reviewed policies; sheets, keys,
flags, original images and accepted media retain their presented hashes.
`scan-acceptance.json` and `scan-acceptance-audit.json` bind the verdict to 106
sheets, 419 images and 555 decoded frames. `scan-approval-evidence/` preserves
the pre-verdict results, reports and viewer. Native run manifests, recording
decisions and original sampled checklists are unchanged. This scan step ran
locally on the receiving Mac; the native sampled scans ran on the separate Mac.
No final-export visual or full-frame privacy verdict remains open for this trial.

## Local evidence and next step

Copied original evidence is in
`takes/separate-machine/reshoot-trials/mac-arm64-8985022-20261021T213321Z/`, with
the supplied `decisions.json` in its parent. Local audit outputs are under
`takes/separate-machine/audit-4f83ba850e73435595b794f6b075e87b/`:

- `audit.py`, `results.json`, `acceptance.json`, `acceptance-evidence/` and
  import-command logs retain technical verification and bound visual acceptance.
- `setup-clarification.json` records the owner's clarification.
- `full-scans/`, scan logs and `scan-review.json` bind full-frame coverage, exact
  export hashes, policies and review evidence.
- `review/scan-sheets.html` is the 106-sheet review viewer.
- `scan-acceptance.json`, `scan-acceptance-audit.json` and
  `scan-approval-evidence/` retain the exact privacy verdict and its verification.

Next, exercise skill discovery in a fresh harness session and a synthetic UI
refresh on the other Mac. Existing accepted macOS and Linux promo media are
unchanged. After completing both reviews, the owner authorized a local checkpoint
commit for these validation records. No new publication is part of this result.
