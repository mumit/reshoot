# Controlled service-change trial

Recorded on October 21, 2026, Vancouver time.

Status: all six controlled cases produced their expected technical results.
The owner accepted all four exact final MP4s with “Accept all four”; their bound
recording and story-beat decisions are imported, and each final run reports
review completed. Two deliberate service faults stopped on the unchanged search assertion
and produced no final export. The owner subsequently reviewed and approved all
four full-frame scan-sheet sets: 391 sheets covering 1,562 distinct images and
all 2,380 decoded final frames. Their saved checklists report review completed.

## Task and fixture

A disposable notes app uses two loopback HTTP origins: a web page on port 18926
and a synthetic API on port 18927. Each preview and final starts a fresh server
with the same three made-up notes. The browser types “Pick up the bikes,” saves
it through `POST /notes`, types “bike,” and searches through `GET /search?q=bike`.
The story checks the saved note, successful search status, exactly one result,
and the matching text. The status assertion prevents an error or stale list from
passing as a successful search.

Only the headless browser page is captured. No real account, file, photo or
external service is involved. The API allows the exact local web origin and
disables caching. Per-run request logs retain the actual status, response body
and elapsed search-response time. Reshoot's browser resource capture does not
archive these JSON API responses, so this supplemental evidence is explicit.

The storyboard, captions, six assertions, six-second search timeout, holds and
export configuration remain byte-identical across all cases. The only client
repair changes `payload.items` to `payload.items ?? payload.results`, retaining
the array check. It is an app-fixture repair, not a reshoot implementation change.

## Cases

| Case | Change | Expected and observed result | Final duration |
|---|---|---|---:|
| C01 | Healthy original service format | Preview and fresh final passed | 8.97 s |
| C02 | Search response delayed three seconds | Preview and fresh final passed; wait retained | 12.73 s |
| C03 | Search returns HTTP 503 | Preview failed on search status; no final | — |
| C04 | Search field renamed from `items` to `results` | Original client preview failed on search status; no final | — |
| C05 | One-line app parser repair, new service format | Preview and fresh final passed | 8.98 s |
| C06 | Original service format restored, repaired client retained | Preview and fresh final passed | 8.98 s |

C03 reports “Search service unavailable”; C04 reports “Unsupported response
format.” Both preserve the native assertion error and failure screenshot. Earlier
passed add-note checks do not establish success of either incomplete flow.
All cases remain in the matrix. No failed assertion was deleted or replaced with
the observed error text. The three later successful finals compare explicitly
against C01, retaining all four beat IDs and definitions without promoting or
inheriting approval from that baseline.

The successful final run IDs are:

- C01: `a2e88bb3a3e84905b3154890a87f535b`.
- C02: `0a5fe8baedc34dffae870492c63ff64b`.
- C05: `fde463e864ed4b349e22e3a5adf9cd33`.
- C06: `7cbb72b7c0ee4c8b8ee1acff2df8bb3a`.

## Evidence and limits

The closing audit verifies 104 native manifest file hashes and 48 passed
assertions across the eight successful runs. All four finals fully decode as
1280 by 720 H.264 at 60 fps. Encoded opening, search and ending frames were
inspected; independent Tesseract OCR verifies the final note/status and the
delayed case's visible “Searching…” state. The API log records its final search
response taking 3.0055 seconds. Full-frame Vision scans cover all 2,380 encoded
frames plus each final's subtitle file, with zero flags or detector errors.
Repeated identical frames share checklist entries. Both owned service ports
were confirmed closed outside the sandbox after the matrix.

The first supplemental OCR assertion expected a space after the numeral “1,”
which Tesseract omitted. The audit now normalizes whitespace for that status
check, retaining raw OCR and the original note-text check; no media changed.
An initial sandboxed port probe was unavailable, so cleanup was verified in an
approved outside-sandbox audit rather than treating denied access as closure.

Local evidence is under ignored
`takes/compatibility-20261020/changing-service/`:

- `protocol.json`, stable input hashes, original and repaired client, and exact
  `client-repair.patch` describe the declared matrix.
- `server.py` and `run.py` provide the synthetic service and recording harness.
- `attempt-94dc59677d9b/` retains tool versions, doctor output, all ten CLI runs,
  case input snapshots, request logs, commands, timings and both expected failures.
- `project/takes/runs/` retains isolated previews, fresh finals, native assertions,
  manifests, comparisons and sampled scan reports.
- `full-scans/` holds supplemental full-frame scans of the four exact final MP4s
  and their subtitle text. Human sheet review is separate from automatic scanning.
- `audit.py`, `results.json`, `presentation.json` and `review/index.html` bind the
  technical results and review presentation to exact exports.
- `acceptance.json`, `owner-decisions/` and `acceptance-audit.json` retain the
  exact owner verdict, four accepted artifact hashes and bindings, imported
  decisions and closing verification. Previews and expected failures retain
  pending review. No baseline was promoted.
- `scan-acceptance.json`, `scan-approval-inputs.json` and `scan-acceptance-audit.json`
  bind “Reviewed all, approved.” to the four full-frame checklists, policies,
  unchanged sheets, original frames, keys and exact final videos. All checklist
  entries are saved as checked. This approval covers the four sets presented;
  earlier trials and other checklists retain their previous states.

This adds evidence for delayed responses, HTTP errors, a schema change, a small
compatibility repair and recovery on one Mac. It does not certify actual remote
services, Internet availability, authentication, TLS, CDNs, rate limits or other
platforms. It is not a novice-user or comparative speed measurement. No manual
video edit, implementation change, commit, push or publication was performed.
