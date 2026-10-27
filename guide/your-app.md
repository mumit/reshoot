# Record your own web app

The quickest route is the [agent prompt](agent-quickstart.md). This page is for
doing it yourself. For a Mac app, see [a macOS window](macos-window.md).

## Show the task

For a simple web app; with a login or data to reset, an agent gets further.
Start the app with made-up data, then give reshoot its address:

```bash
reshoot create http://127.0.0.1:3000/ --directory demo
```

In the browser that opens, show one task:

- **Caption here** explains its outcome.
- **Check result** selects the visible result without activating it.
- **Hide** selects an element to blur in every recording.
- **Pause** leaves interactions out; restore the app's state before resuming.
- **Remove last step** removes a step; restore its app state before repeating it.

Choose **Done**. reshoot writes the project, records a preview and opens the
studio. Result checks it suggests are marked `# suggested` in
`demo/storyboard.toml`: remove any that aren't the result, then choose
**Update preview**, and **Make final** when ready.

Multiple-choice lists, file selection and drops are saved as steps with a
`recording_issue`, which can't be recorded. Add their actions in
`storyboard.toml` and remove the `recording_issue`.

## Choose one result

Keep the first demo [small](agent-quickstart.md#start-with-one-prompt). Fill in
`BRIEF.md` first:

```text
Audience: Developers evaluating a task app
Problem: Finding one unfinished task in a long list
One task: Add a task, then filter to its matching result
Visible proof: The saved task is the only result
Destination: A short README loop with captions
Next action: Try the app
```

Give the app its own demo data and a way to reset it. If a response is mocked,
say so in the brief.

## Create the project

From the app repository's root, or an empty folder for a URL-only app:

```bash
reshoot init demo --url http://127.0.0.1:3000/
```

This writes `BRIEF.md`, `storyboard.toml`, `edit.toml` and `reshoot.toml`.
Either leave your server running, or let reshoot start and stop it with an
`[app]` table in `demo/reshoot.toml`:

```toml
[app]
run = "cd .. && npm run dev -- --host 127.0.0.1 --port 3000"
url = "http://127.0.0.1:3000/"
timeout = 60
reset = "MY_DEMO_RESET_COMMAND"
```

Commands run from `demo/`. `reset` runs before startup and must touch only
demo data. Stop any server already on that port.

### With only a URL

Leave out `[app]`; reshoot records the site at the URL, local or hosted. Use a
test account with made-up data. Without a reset, each recording adds another
saved item, so check that the new item is shown rather than an exact total.

## Write a checked story

For an app with a task box, an Add task button, a search field and a task
list; use your app's targets:

```toml
schema_version = 1
id = "tasks"
url = "http://127.0.0.1:3000/"
size = "1280x720@1"
seed = 1

[[beat]]
id = "intro"
caption = "Find the task you need"
hold = 1.5

[[beat]]
id = "add"
purpose = "Save a task and show it in the list"
hold = 1.5
[[beat.action]]
type = "type"
target = {role = "textbox", name = "New task"}
text = "Prepare the release notes"
[[beat.action]]
type = "click"
target = {role = "button", name = "Add task"}
[[beat.expect]]
type = "text"
target = {test_id = "task-list"}
contains = "Prepare the release notes"

[[beat]]
id = "search"
purpose = "Show only the saved task"
caption = "One matching task"
hold = 2.5
[[beat.action]]
type = "type"
target = {role = "textbox", name = "Search tasks"}
text = "release"
[[beat.expect]]
type = "count"
target = {css = "[data-testid='task-list'] li"}
count = 1
[[beat.expect]]
type = "text"
target = {test_id = "task-list"}
contains = "Prepare the release notes"

[[beat]]
id = "end"
hold = 0.5
```

Replace all of `demo/storyboard.toml` with it. Keep the `end` step: the
generated edit stops there.

Find targets in the source or the browser's inspector. A role and name work
when they match one control; so does a `data-testid` or stable CSS. reshoot
fails on a missing, covered, disabled or ambiguous control rather than forcing
a click: fix the target or app state, not the result check. When a control
changes, [repair the step](studio.md#repair-a-step-that-broke).

## Draft it by clicking through

```bash
reshoot rec http://127.0.0.1:3000/ demo/draft.toml
```

Do the task in the browser that opens, then close it. The draft has your
actions as steps and suggested result checks, with the same limits as
**Show the task**. Keep the checks that show the result, add captions, rename
steps such as `click-albums`, and use it as `demo/storyboard.toml`. The [project reference](projects.md#storyboardtoml)
lists every action and check.

## Login and demo data

Every recording starts with a fresh browser profile. For a login, use a demo
account and `[[setup]]` actions, which run before the recorded steps:

```toml
[[setup]]
type = "navigate"
url = "http://127.0.0.1:3000/demo-login"
```

Your app must provide that demo login. Never commit real credentials. `blur = ["SELECTOR"]` can hide a demo header, but is no
substitute for demo data.

Declare fixture files inside `demo/` with top-level `inputs = ["seed.json"]` in
`reshoot.toml`, before any table, so **Update preview** records again when they
change. For an external database, use **Record app again**.

## Record it

```bash
reshoot doctor --config demo/reshoot.toml
reshoot preview demo/reshoot.toml
reshoot run demo/reshoot.toml
```

If a step fails, see
[troubleshooting](troubleshooting.md#an-action-or-result-check-fails). For a portrait export, crop or
record a mobile size: squeezing a wide page into a phone frame makes its text
unreadable. To update it later, see [keep a demo current](publish.md).
