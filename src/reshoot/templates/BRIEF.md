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

From the folder that holds `demo/`:

    reshoot preview demo/reshoot.toml    a quick, smaller recording to check
    reshoot run demo/reshoot.toml        the final
    reshoot accept demo/latest --export docs/demo   once you've watched it

Each run ends with the paths of its video, GIF and review page. Nothing is
published. Commit `demo/`, including `demo/accepted/`; `demo/.gitignore` keeps
the recordings in `takes/` out.
