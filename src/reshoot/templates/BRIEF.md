# Demo brief

- Audience:
- Problem they recognize:
- One task to show:
- Visible result that proves it worked:
- Why the result matters:
- Destination and length:
- What the viewer should do next:

Use made-up data only. The bundled notes app resets when the page reloads.
For another app, document its separate demo account or database, reset command,
and expected result before changing the storyboard. Log mocked responses explicitly.

Run `reshoot doctor --config reshoot.toml`, then `reshoot preview reshoot.toml`.
Run `reshoot run reshoot.toml` for the final recording. Each run prints its report path.
Review the complete final video. A successful command is not publishing approval.

New storyboards use TOML native actions with explicit expected results. The edit file
selects ranges by beat name and can declare output profiles. Use `reshoot review RUN`
for the local review page and `reshoot compare OLD_RUN NEW_RUN` for matching beats.
Review IDs and media hashes must match before importing decisions.
