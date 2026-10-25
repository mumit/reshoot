# Explicit locator repair

On 2026-10-24, the local macOS checkout was exercised with synthetic notes
data to verify the visual repair milestone in the [creation and revision
plan](../../UX_PLAN.md). These are automated and agent-operated checks, not
independent-user research or owner acceptance of media.

## What changed

The recorder saves stable alternative locators alongside the original target.
A failed run can suggest a replacement only when unique, visible, compatible
alternatives agree on one element. The recording still fails. Wrong result
values and count mismatches never become suggested locator repairs.

`reshoot repair RUN --apply` replays the prefix and revalidates the suggestion
against the current app. `--pick` lets the user select a replacement without
activating it, then confirm with **Use this control**. The studio exposes both
routes beside the failure frame and labels any previous successful recording.

A repair changes only the target of the failed operation. It preserves typed
text, operation types, expected values, other checks and source comments.
Source revisions reject stale edits; an audit record retains the before and
after hashes. Studio repairs participate in Undo/Redo. A fresh preview must
verify the task afterwards; the original failed run stays failed.

## Synthetic app trial

The packaged notes app was recorded, then its search input was renamed from
`#q` to `#search-input`. Its recorded placeholder alternative remained valid.

| Stage | Evidence |
|---|---|
| Baseline | Run `0fbdafee9e3544b5b1e58fea8dbb8c36`; 3 checks passed |
| Renamed control | Run `483384cbddc84b9185f17c8b2bf65753`; stopped on the missing `#q` target |
| Explicit repair | Revalidated the placeholder alternative and changed only the locator |
| Fresh preview | Run `78baacea0e9e401db2076db8a3b98372`; 15 seconds, all 3 original checks passed, 6 scan items, 0 flags |

The original expectation arrays were compared with the repaired storyboard and
were unchanged. The studio failure panel, friendly suggestion and picker were
inspected. After the fresh preview, the studio showed that run and removed the
failure panel. Generated evidence remains under the ignored
`takes/locator-repair-20261024/` directory. No sample was accepted or published.

## Verification

| Check | Result |
|---|---|
| `uv run pytest -q` | 123 passed, 42 browser tests deselected |
| `uv run pytest -m browser -q` | 42 passed, 123 fast tests deselected |
| Wheel build | Passed; repair Python and JavaScript assets included |
| Plugin validation | Passed with existing root context and missing icon warnings |
| Changed-document relative links and TOML examples | 116 links/anchors and 18 snippets or alternatives checked |
| Python compilation, JavaScript syntax and whitespace checks | Passed |

The regression cases cover renamed controls, agreeing and conflicting
alternatives, ambiguous primary locators, separate shadow roots, incompatible
controls, stale suggestions and source files, cancellation, source comments,
exact setup/check slots, unavailable audit storage, and studio repair followed
by undo, redo and a fresh preview. Picking suppresses pointer and click events
so selecting a control does not activate it.

An earlier complete browser run found an assertion that treated a relative
media URL as absolute. The assertion now checks the browser's resolved URL;
the complete studio browser trial passed after that correction.

## Limits

Visual picking currently selects controls on the main page. Iframe targets
need a manual source edit or a revalidated recorded suggestion. Count-query
failures need the app, data or storyboard fixed rather than selection of a
single replacement element.

Prefix replay can modify the demo app, so use resettable synthetic data.
Source hashes do not snapshot an external service or database. The tests and
trial ran on macOS; this adds no Linux or Windows compatibility evidence and
does not establish ease of use for a newcomer.
