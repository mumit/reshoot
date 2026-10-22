# Try a release comparison

For a complete installation, repair, review and export walkthrough, start with
the [project tutorial](../../guide/step-by-step.md). These commands are a shorter
repository-based example; they run from the reshoot checkout's root and need
the [browser installation](../../guide/install.md).

Both versions use made-up notes. Version 2 changes the app heading and the save
button label. The task and expected results stay the same.

```bash
reshoot run examples/notes/release-v1.toml
reshoot run examples/notes/release-v2.toml
reshoot compare FIRST_RUN SECOND_RUN --out comparison.json
reshoot review SECOND_RUN --previous FIRST_RUN
```

Replace `FIRST_RUN` and `SECOND_RUN` with the folders printed by the commands.
The local page shows the exact videos and matching beat evidence. A matched ID
does not mean unchanged pixels or verified behavior; inspect the result records.
The browser version is recorded, and the baseline is chosen explicitly.
`reshoot review` prints the generated `SECOND_RUN/review.html` path. Open it
in a browser, watch both final exports and inspect the beat evidence. It does
not automatically open a browser or import an approval.
