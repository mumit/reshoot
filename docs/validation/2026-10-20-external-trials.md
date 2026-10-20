# Synthetic external trials

Date: 2026-10-20

The owner authorized finding public GitHub projects and offered photosearch. I used
four repositories, with two TodoMVC variants, in isolated clones. These are automated
synthetic workflow trials, not maintainer or user acceptance studies. No real
accounts, photographs, Photos libraries, or private project data were used.

The [resume validation](2026-10-20-resume-validation.md) records the host, tests,
fresh harness sessions, and fixes. The owner has now accepted the five selected
candidates; see [Owner acceptance](#owner-acceptance). The proposed 15-minute and
eight-of-ten product targets remain unmeasured.

## Sources and fixtures

| Repository | Pinned commit | App and useful task |
|---|---|---|
| [tastejs/todomvc](https://github.com/tastejs/todomvc) | `ff43b02e59dfa604386bb382034b2cd07c2bcd8a` | JavaScript ES5: add a bikes task, check it, filter completed tasks |
| Same TodoMVC checkout | Same commit | React: the same task through controlled inputs |
| [pallets/flask](https://github.com/pallets/flask) | `d086db856be187255b8ec61ef409357393020f32` | Flaskr tutorial: sign in with a synthetic local account and save a post |
| [simonw/datasette](https://github.com/simonw/datasette) | `c435a800306987ef1d034f84f685b826153b55a5` | Browse three generated SQLite rows, filter two pending tasks, query them in VHS |
| [mumit/photosearch](https://github.com/mumit/photosearch) | `f73bd0f5dc1b9652f591ccbb1653ab339d45d2a3` | Search generated thumbnails with a mocked embedding model and open a result |

Clones live under `/private/tmp/reshoot-external-20261020/repos/`. The owner's
original photosearch checkout was read only. Its ignored `data/` and `data-demo/`
were not copied. Photosearch uses the clone's test-library generator for 73
synthetic entries and generated abstract thumbnails. The adapter sets its index
path before imports and checks that imported server code and the data path belong
to the isolated clone. It blocks Photos and model-package imports, mocks query
embedding, disables Photos fetch/album operations, and uses no Jev key. This tests
recording and app interaction, not search quality, model loading, or Photos access.
The captions identify the mocked model and generated images.

A separate Python 3.12 environment contains Flask 3.2.0.dev0, Flaskr 1.0.0,
Datasette 1.0a41 from the pinned checkouts, and sqlite-utils 4.2.1. Dependency
versions are saved in `external-dependencies.json`. Photosearch uses installed
packages from the owner's existing Python environment, with bytecode writing
turned off; its source and index come from the trial clone. Its dependency versions
are saved separately. React uses its checked-in `dist` bundle, with no npm build.
Its manifest and README disagree about React versions, so I do not claim a verified
runtime version. ES5 uses its locked npm dependencies, installed with scripts disabled.

## Start and reset

Each project has a brief, TOML storyboard with stable IDs and native assertions,
an edit file, and versioned `reshoot.toml`. All browser contexts are fresh.
The app commands bind loopback ports and reshoot stops each server before returning.
Commands below run from each project's root; environment paths refer to the isolated
trial environment, not a system installation.

| Project root beneath `repos/` | Startup | Reset |
|---|---|---|
| `todomvc/examples/javascript-es5` | `python3 -m http.server 19371 --bind 127.0.0.1` | Fresh browser context clears this trial's local storage |
| `todomvc/examples/react/dist` | `python3 -m http.server 19372 --bind 127.0.0.1` | Fresh browser context |
| `flask/examples/tutorial` | `venv/bin/python trial_app.py` | `venv/bin/python seed.py` recreates only `trial.sqlite` and the demo account |
| `datasette/reshoot_trial` | `venv/bin/datasette serve demo.db --template-dir templates --host 127.0.0.1 --port 19374` | `venv/bin/python seed.py` recreates the tasks table from `fixture.json` |
| `photosearch/reshoot_trial` | `PYTHONDONTWRITEBYTECODE=1 OWNER_ENV/bin/python trial.py` | Same interpreter and flag with `trial.py --seed`, recreating only `demo-index` |

The VHS take queries `demo.db` with
`sqlite-utils demo.db 'select title from tasks where done=0' --table`. It starts
an `env -i` shell with a generic prompt, explicit tool PATH, no history, and no
shell startup files. Directory setup is hidden. It neither reassigns HOME nor
captures anything outside its terminal. The browser has native expectations;
the VHS result is checked by frame inspection, not by a native assertion.

Setup and authoring were performed by this agent, without a maintainer or novice
following the workflow. End-to-end setup and first acceptable preview time were
not measured. The timings below cover the CLI command after dependencies, fixture
adapters, and storyboards existed.

## Failures and repairs

I kept the original logs, reports, and available failure images.

1. **Missing TodoMVC CSS.** The first ES5 preview was unstyled but passed its task
   assertions. Frame inspection caught the missing npm assets. `npm ci --ignore-scripts`
   installed the locked dependencies after a sandbox/cache failure and an authorized
   retry. This demonstrates that passed task assertions do not establish appearance.
2. **Ambiguous photosearch target.** `#grid .tile:first-child` matched one tile in
   each row. The first preview failed a strict visibility assertion. I changed both
   targets to `#grid .tile[data-i='0']`, preserving the intended first result and checks.
3. **Overlapping photosearch tiles.** The next preview completed its search checks
   but native click refused an intercepted target. The pinned app's judge-view
   `.jrow` CSS rules also affected the photo grid. I scoped those judge rules to
   `#jroot` in the trial clone. No forced click or assertion removal was used.
   The patch is saved with the trial recipes; the owner's checkout is unchanged.
4. **Mixed preview sizes.** Datasette's browser-plus-terminal preview recorded both
   takes, then failed editing because browser preview was 720 by 404 and VHS was
   1280 by 720. Reshoot commit `c38805d` retains browser dimensions for previews
   containing VHS. The repaired preview and final runs passed. The failed edit
   honestly retains passed browser assertions, failed execution, and skipped scan.

5. **Captions lost on page loads.** Flaskr's exports lost their on-screen captions
   while writing and after saving, despite passed task checks. Reshoot commit
   `1f26c1f` restores captions across same-origin page loads. The selected Flaskr
   IDs below are new preview, baseline, and changed-heading runs after the fix.
   Earlier batch candidates and full scans are retained as historical evidence.

## Runs and comparisons

All five repaired previews, five baseline finals, and five changed-UI finals
completed with their configured browser expectations passed and sampled Vision
scans completed. At the end of the automated trials, every run left human review
pending. The selected refreshed candidates now have owner acceptance recorded
below. There was no manual video editing. The setup repairs above were necessary
before these successful runs.

Refreshes changed only UI presentation in the clone: ES5 heading, React heading
color, Flaskr form heading, Datasette index heading, and photosearch brand label.
The storyboards, task meaning, and expected results were preserved. Each refresh
uses the recorded baseline explicitly for `reshoot compare` and `reshoot review`.
All four beat definitions match in each comparison. Datasette reports changed
actual result text because its body assertions also capture changing query-time
footers; the same row-count and required-text assertions pass. A matched ID is not
a verdict that pixels or results are identical.

The five small presentation changes do not establish success over ten agreed
updates, API changes, or broader selectors and timing problems.

| Variant | Repaired preview | Baseline final | UI refresh final | Browser assertions |
|---|---:|---:|---:|---:|
| todomvc-es5 | 14.00 s | 14.80 s | 14.78 s | 4 |
| todomvc-react | 13.36 s | 14.46 s | 14.58 s | 4 |
| flaskr | 17.63 s | 19.12 s | 18.76 s | 3 |
| datasette | 34.62 s | 34.65 s | 34.94 s | 4 |
| photosearch | 21.78 s | 25.36 s | 30.89 s | 4 |

Timings include capture, encoding, edits, reset/startup, and sampled scans. They
exclude dependencies, story authoring, repairs, comparison, and human review.

| Variant | Baseline ID | Refreshed candidate ID |
|---|---|---|
| todomvc-es5 | `b8c1bbc7b59044f3a959316b879b52fa` | `6511a4d3c64749ddadd6740c4933ffc4` |
| todomvc-react | `a0725dd714bf44b390a901981d2e2e4d` | `923d2075845948758d282f2fd97d6460` |
| flaskr | `262953f8da294c0c8be01a59cbe5c4bc` | `cae71dad35c14af7b88bbdd9e42445c0` |
| datasette | `e88e4c9aa04b461caa2ef9889629d604` | `6c23cbb4e36b4996ab7d5ff38c9b707c` |
| photosearch | `c95d85029fa64f72b5a0a8e3c34b75e9` | `a404a6bbbcb44fc698301a7aa67e6374` |

Each ID is beneath the project root at `takes/runs/ID/`. The candidate contains
`run.json`, `comparison.json`, `review.html`, and `takes/demo-final.mp4`. Datasette
also retains `takes/terminal.mp4`. Use the saved projects to open the HTML locally.

## Inspection and limits

I inspected frames extracted from actual previews and both baseline/refreshed
final exports, including the completed TodoMVC task, saved Flaskr post, Datasette browser filter and terminal
result, and photosearch search grid and lightbox. Captions and useful results fit
in the inspected frames. These clips are silent. At that point, complete playback
and owner judgment of timing, readability, and privacy were pending. Beats without
assertions remain individually unverified. Photosearch
home-page selection varies between runs; its underlying fixture library and
search task stay fixed. Changed evidence is not automatically a regression.

Each run's original check samples the final MP4 and GIF every three seconds and
checks exact generated subtitle text. Those checks do not include every possible
photo or every decoded frame. Supplemental offline checks of refreshed candidates
scan every decoded MP4/GIF frame, their evidence images, all saved photosearch
image resources, and exact subtitle files. Their reports are separate from the
original run's sampled check and do not transfer decisions or approval.

| Candidate | Full-scan time | Decoded frames and supplied images | Pending items | Flags |
|---|---:|---:|---:|---:|
| todomvc-es5 | 49.30 s | 607 | 392 | 0 |
| todomvc-react | 47.21 s | 609 | 386 | 0 |
| flaskr | 47.02 s | 662 | 405 | 0 |
| datasette | 78.22 s | 1024 | 630 | 0 |
| photosearch | 128.74 s | 684 | 681 | 0 |

All supplemental checks completed with Vision text and people requests on macOS
27.0.1. They returned exit 1 because review is pending, with no detector errors.
The first five full checks failed their initial Vision request inside the sandbox
with `Vision failed (unknown unknown)`. Those reports were retained, and authorized
retries outside that sandbox completed. This is a permission/environment boundary,
not evidence of reliable scanning inside the sandbox. Zero flags do not establish
privacy safety or positive face/person detector accuracy. All manifest artifact
hashes still match after scanning and inspection.

Photosearch's existing recording method is documented in its pinned
[`tools/launch/README.md`](https://github.com/mumit/photosearch/blob/f73bd0f5dc1b9652f591ccbb1653ab339d45d2a3/tools/launch/README.md):
a Python headless storyboard, VHS Claude take, one Photos window, image sheets,
and Python cuts. I read that method but did not execute it against Photos or time
it. The other projects' maintainers did not supply recording methods. No measured
time saving or comparison with their prior method follows from these trials.

## Owner acceptance

On 2026-10-20, after reviewing the selected candidates through the local index,
the owner said: "I've accepted all of these, but don't want to download and rename
these files. Go ahead."

I generated one decisions file for each refreshed candidate listed above and
imported it through `reshoot review --import-decisions`. Each file accepts the
video and four named beats, for 25 decisions across five candidates. Before
importing, I verified that each reviewed copy and original run had matching
artifact hashes, decision names, and policy bindings. After importing, both copies
of every selected run report `review_status: completed`. I verified the manifest
hashes again and refreshed the comparison review pages with the saved decisions.

The local record is `takes/validation-20261020/owner-acceptance/receipt.json`,
with per-candidate `decisions.json` files and backups of the prior review metadata.
The review index links to that record. The earlier evidence archive remains a
snapshot from before owner acceptance.

This completes owner acceptance of the five selected external candidates.
The measured user targets and broader compatibility work below remain open.

## Evidence and next acceptance work

Run paths and IDs identify the exact candidates. Each final MP4, GIF, subtitle,
poster, native take result, evidence image, and saved resource retains its recorded
hash. Baseline selection stays explicit. Review pages are generated after servers
stop and use saved frames. Owner decisions for the five selected refreshed
candidates are now imported as recorded above.

`takes/validation-20261020/` contains initial, corrected, and repaired preview logs,
baseline and refresh records, recipes, app patches, runner scripts, dependency
versions, comparisons, scans, and extracted frames. Temporary checkouts and heavy
dependencies are not committed. These trial files use host paths; recreate their
environment and pinned sources before reusing them.

Remaining acceptance work is timed user setup and review, maintainer-method
comparison, and ten agreed update cases. Compatibility beyond
this host, real changing services, positive face/person detection, native-window
trials here, and longer animated recordings remain open. The local review index is `takes/validation-20261020/index.html`. The
[resume validation](2026-10-20-resume-validation.md) lists the optional ignored
evidence archive and its checksum. No release or demo media publication occurred.
