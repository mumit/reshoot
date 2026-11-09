# State-machine audit and shared workflow validation

Date: November 8, 2026. Base: `c04bc01` (0.3.14).
Local branch: `refactor/workflow-state`.

The [architecture inventory](../architecture/state-machines.md) identifies 31
state-bearing lifecycles and explains their ownership, transitions and remaining
boundaries. This work concentrates on shared workflow decisions and studio jobs.
It does not claim to replace every local interaction loop or prove that no
regression is possible.

## Delivered behavior

| Experience | Change | Observable result |
|---|---|---|
| UX | Shared action rules for creation, tools, history and active jobs | Page controls and HTTP guards use the same capability decisions; history recovery remains available when ordinary editing is blocked. |
| UX | Explicit starting/running/cancelling/finishing/terminal job phases | An observed job can be cancelled; a stale cancellation cannot stop a newer job, and a finishing or completed repair is not relabelled cancelled. |
| DX | Project observations and update selection moved out of `studio.py` | `workflow.py` and `journey.py` own those rules; existing studio helper imports remain available. |
| DX | One editable source set | Studio history, demonstration drafts and status inspect the same project files. |
| AX | `reshoot status PROJECT --json` | Schema version 1 reports durable state, separate outcomes, capabilities/reasons and suggested next commands without executing them. |
| AX | Explicit observation limits | Tool readiness, live studio jobs and unsaved browser fields are unknown to disk-only inspection rather than silently treated as ready/idle. |

No existing project, run, creation, demonstration or editing-history schema was
migrated. Human review and acceptance remain separate from execution and scanning.
The CLI's explicit preview-review option remains available.

## Verification

Commands use the existing checkout environment and synthetic fixtures. Local
HTTP/browser integration checks ran outside the agent sandbox so they could bind
ports and start Chrome. Tesseract was selected explicitly for test scanning.

| Check | Result |
|---|---|
| Baseline fast suite | **359 passed, 66 deselected** |
| Final fast suite | **386 passed, 67 deselected** |
| New workflow contracts, included in the fast suite | **27 passed** |
| Focused narration and framing browser rerun | **2 passed, 26 deselected** |
| New reopening/cancellation browser regression | **1 passed, 27 deselected**; verifies restored controls, cleared explanations and accurate first-preview wording. |
| Complete existing browser suite | **66 passed, 385 deselected**, followed by the separate new browser regression above: **67 distinct browser cases passed** overall. |
| Python compatibility | Modified Python sources parsed with Python 3.11 grammar; this is a syntax check, not a Python 3.11 runtime run. |
| Studio JavaScript | Generated script passed `node --check`. |
| Package | Source archive and wheel built; new workflow/job modules and updated skills are included. |
| Wheel smoke | Wheel extracted to a temporary directory, imported outside the checkout, and successfully produced status JSON using existing interpreter dependencies. This is not a clean dependency installation. |
| Plugin/skills | `claude plugin validate .` passed with existing root-context and missing-icon warnings, plus marketplace-install advice. |
| Visual inspection | Test-generated desktop editing, mobile comparison and running/cancelled job views inspected. |
| Local documentation | 28 relative file links checked; no broken files, unbalanced code fences or em dashes in the checked documents. |

The new contracts cover capability precedence, independent acceptance/tool state,
no-write/no-probe status, matching CLI/studio update decisions, history recovery,
malformed creation data, concurrent HTTP job guards, stale cancellation, cancel
before process startup, finishing callbacks, callback failure and subsequent jobs.
A separate regression keeps missing tools visible in live state after an earlier
successful recording.

## Intermediate failures and corrections

The first broad browser attempt found that disabling the update button for
unsaved fields hid the existing actionable explanation in narration and framing.
The established behavior was restored. A focused rerun then found that applying
the ordinary edit guard to the recovery action prevented recovery itself. Recovery
now uses its own shared capability. Both focused browser journeys passed after
these corrections.

The obsolete full-suite process, which had imported the earlier implementation,
was stopped and a clean full run was started. Its interrupted result is not a
passing suite or an additional product defect. No result check or expectation was
weakened to make the corrected browser journeys pass.

The initial offline package build lacked cached build dependencies. The declared
build dependencies were fetched, the build succeeded, and the final offline
rebuild succeeded. No runtime dependency was added.

The new browser fixture initially omitted the readiness report's `checks` list;
the fixture was completed and the browser test passed. A final copy correction
was checked in that regression: before any successful recording, cancellation
preserves the saved story rather than referring to a previous video. Partial
preview cancellation is also described as cancelled rather than failed.

## Review corrections, November 9

A review of this branch found problems the checks above missed, now fixed:

- Opening the studio during an update and then cancelling it left the editing
  panel disabled until a reload, because the server sent the panel locked and
  the page never unlocked it. The browser regression now checks the panel.
- `status` offered actions with nothing to act on, such as Repair control with
  no stopped step, and suggested commands that open a page for a person without
  saying so. Actions now apply only where they can, `waits_for_person` marks
  interactive ones, and step actions show their command with `STEP`.
- Enabled buttons lost their explanations; they keep them again.
- A cancel that arrived after the update finished replied as if it worked.
- The demo skill had dropped the rule that a recipe is not a verified result.

`uvx --python 3.11 python -m compileall -q src tests` passed, which the syntax
check above did not cover.

## Second audit, November 9

Three read-only passes covered the browser scripts, the recording and review
pipeline, and the studio's editing flows. Each lead was read in the code before
changing anything; two were wrong and are not fixed: pending history recovery
already refused every change on `main`, and the first Cancel cannot skip the
job check because the button is hidden until the job is known. Eighteen defects
were fixed, as listed in the [architecture record](../architecture/state-machines.md#second-audit-november-9).
Twelve have a new or extended test that failed against the code before the
fix and passes after it. The pull-request comment was checked by running the
workflow step's script with `gh` stubbed, once for each outcome. The other five
were checked by reading and by the existing suites only, with no test of their
own: the page recovering from a failed
status check, Accept and Cancel sent once, newer text staying marked unsaved,
the saved-source download outside the lock, and `run.json` and
`decisions.json` replaced whole.

## Artifacts and limits

Local generated script/status evidence is under ignored
`takes/state-machines-20261108/`. Existing synthetic notes runs from the November 5
review were used for an additional read-only status smoke. Automated browser
fixtures create their own isolated projects and media in pytest temporary folders.
These local artifacts are optional evidence, not prerequisites for reading the
architecture record or running the tests.

There was no independent usability trial, new Linux/Windows run, external app
trial, publication or owner acceptance of media. Several browser fixtures disable
OCR for speed; Tesseract checks do not establish face/person detection. Existing
accepted media under `docs/demo/` was not replaced.

Live jobs remain local to each studio server. Disk-only status cannot coordinate
other servers or CLI processes, infer unsaved fields, validate remote app state or
prove a demo is safe to share. Capability output does not replace authorization,
fresh request checks or human review.
