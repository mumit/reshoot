# Record a running web app

Use this route when you have a URL, even without the app's source code. Reshoot
records the actual site in a fresh headless browser. Keep the demo files in
their own folder; the site can stay hosted elsewhere.

For the shortest route, use the [agent quickstart](agent-quickstart.md) and set
`Target:` to the URL. Add one task and a demo account if the site needs login.
The agent can inspect the page's controls instead of reading source code.

## Prepare the target

Open a local work folder for the demo. Use a test environment or an account
containing only made-up data. Choose a small task such as creating an item and
finding it by search. Confirm that it can be repeated and document how to reset
its data. A saved item on a hosted service persists after recording unless the
app or your reset removes it. Without a reset, the preview and the final each
add one: write result checks that still pass then, such as the new item being
shown, and avoid exact totals.

Reshoot does not reuse your normal browser's login. Provide an isolated demo
login flow that works in a fresh profile. Keep credentials outside committed
files. See [authentication and fixtures](your-app.md#authentication-and-fixtures).
If login cannot be automated yet, resolve that before promising an unattended
recording. Do not substitute a mock page for the requested app.

## Draft the story with the CLI

After [installing the tools](install.md), replace the example URL with yours:

```bash
reshoot init demo --url http://127.0.0.1:3000/
reshoot rec http://127.0.0.1:3000/ demo/draft.toml
```

The second command opens a fresh browser for you to perform the task. Close
that browser when finished. It drafts supported actions; it does not complete
the story's captions, expected results or edit. Unsupported interactions fail
explicitly; see the [recorder limits](your-app.md#write-a-checked-story).

Read `demo/draft.toml`. Use it to replace the placeholder in
`demo/storyboard.toml`. Add a caption, stable beat IDs, explicit result checks
and a hold long enough to read the result. Keep a final beat named `end`, since
the generated edit uses it as its endpoint. Use the
[complete checked story](your-app.md#write-a-checked-story) as a model, replacing
its targets with the actual page's accessible roles, names or CSS selectors.

Alternatively, author the story directly after inspecting the page's DOM.
`init --url` creates a draft, not a working task for an arbitrary website.
Fill in `demo/BRIEF.md` with the task, expected result and reset instructions.

## Record and inspect

```bash
reshoot doctor --config demo/reshoot.toml
reshoot preview demo/reshoot.toml
```

Inspect the printed run folder and actual MP4 and GIF. Repair the story or
setup if the actions or result fail. Then make a fresh final:

```bash
reshoot run demo/reshoot.toml
```

No `[app]` table is generated for this route. Reshoot uses the server already
running at the URL and leaves it running. For a local server, keep its terminal
open. If you later have startup commands, add managed startup using the
[source-app walkthrough](your-app.md#create-the-project).

Follow the [recording and scan-sheet review](step-by-step.md#4-accept-the-recording)
before sharing. Keep the URL, browser story and exact accepted run so you can
[update the demo](publish.md) when the site changes.

Next: [explore the features](features.md), then [customize the result](customize.md).
