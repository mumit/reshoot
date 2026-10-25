# Record your own web app

The shortest route is to [paste the first-demo prompt](agent-quickstart.md)
into Codex or Claude Code and let the agent write these files. Use this page to
write them yourself, or to guide the agent's choices. It covers an app whose
source you have and one you can only reach by URL. For an installed macOS app,
see [Record a macOS window](macos-window.md).

[Install reshoot](install.md) first. The [notes tutorial](step-by-step.md) is
a complete example to try separately; it is not a prerequisite.

## Show the task

This suits a simple web app. For anything with setup, such as a login, a
database to reset or images that take a while to load, an
[agent](agent-quickstart.md) gets further on its own.

Start the app on your computer as you do when developing it, such as with
`npm run dev`, using a demo account and made-up data. Then give reshoot the
address it prints:

```bash
reshoot create http://127.0.0.1:3000/ --directory demo
```

Use made-up data in a separate demo account. The browser starts with a fresh
profile. Show one task, use **Caption here** to explain its outcome, and
**Check result** to select the visible result without activating it. **Hide**
selects an element to blur in every recording. **Pause** leaves interactions
out; restore the app's state before resuming. **Remove last step** removes the
step from the script, so restore its app state before repeating it.

Choose **Done**. Reshoot writes the project, records a preview and opens the
studio. The recorder also suggests result checks from what each step changed
on the page, marked `# suggested` in `demo/storyboard.toml`. If the preview
stops on one that isn't the result, remove it there and choose **Update
preview**. Change captions and holds there, then choose **Update preview**.
Choose **Make final** when ready to inspect the full-size exports and scan
sheets. Nothing is accepted or published automatically.

Checkboxes and radio buttons replay their chosen state. Multiple-choice lists,
file selection and drops are saved as unresolved steps; the rest of the story
is kept. Add the required actions in `storyboard.toml` and remove that beat's
`recording_issue` after repairing it. A story with unresolved steps cannot be
recorded. The manual route below covers startup, reset and login setup when
your app needs them.

## Choose one result

Before writing actions, fill in `BRIEF.md`. For example:

```text
Audience: Developers evaluating a task app
Problem: Finding one unfinished task in a long list
One task: Add a task, then filter to its matching result
Visible proof: The saved task is the only result
Destination: A short README loop with captions
Next action: Try the app
```

Choose demo data that makes the result easy to see. Give the app its own demo
database or fixture folder, with no connection to real accounts or files.
Document how to reset it before each recording. If a response is mocked, state
that in the brief and wherever the demo's claim requires that context.

## Create the project

From the app repository's root, or from an empty folder for a URL-only app:

```bash
reshoot init demo --url http://127.0.0.1:3000/
```

This writes `BRIEF.md`, `storyboard.toml`, `edit.toml` and `reshoot.toml`. It does
not copy the notes app or start the app. Replace the story's placeholder caption
with actions and result checks before recording a demo.

Start the demo server and leave it running, or let reshoot manage its
lifecycle. For the second option, add an `[app]` table to `demo/reshoot.toml`.
For a JavaScript app one level above `demo/`, this is an example to adapt:

```toml
[app]
run = "cd .. && npm run dev -- --host 127.0.0.1 --port 3000"
url = "http://127.0.0.1:3000/"
timeout = 60
```

The command runs from `demo/`, so `cd ..` reaches the app repository. Replace
the command with the app's actual startup command and install its dependencies
first. Keep the URL in this table and `storyboard.toml` consistent.

To reset data, add `reset = "MY_DEMO_RESET_COMMAND"` inside `[app]`.
Replace that placeholder with a command that affects only demo data. Reset
runs from the same directory before startup and defaults to a 30-second timeout.
An existing server must be stopped when `[app]` manages startup. Without `[app]`,
reshoot uses the existing server and leaves it running.

### With only a URL

Leave out `[app]`; reshoot records the site already running at the URL, local
or hosted, in a fresh headless browser. Use a test environment or an account
that holds only made-up data. Find out how to reset its data. A saved item on a
hosted service stays after recording unless the app or your reset removes it.
Without a reset, the preview and the final each add one, so write result checks
that still pass then, such as the new item being shown, and avoid exact totals.

## Write a checked story

Here is a complete story for an example app with a task textbox, an Add task
button, a search field and a task list. The app must actually provide these
controls. Replace the example targets with the ones in your app.

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

Replace the entire placeholder `demo/storyboard.toml` with the new story. The
generated edit ends at the start of the `end` beat, so keep that ID unless you
also change the edit. Named result beats and their holds keep the proof readable.

Find targets in the app's source, or in the browser's inspector when you have only the URL. An accessible role and
name work when they identify one control; a stable `data-testid` also works.
Use CSS when that is the clearest stable target. Reshoot fails on missing,
covered, disabled or ambiguous controls rather than forcing a click. Repair
the target or app state instead of removing the result check.

The recorder saves alternative locators for future repairs. If the app renames
a control, the studio shows the failed step and lets you select its replacement;
see [Repair a changed control](studio.md#repair-a-step-that-broke). From the
CLI, inspect the failed run with `reshoot repair RUN`, then use `--apply` for a
suggestion or `--pick` to choose the replacement. Result checks still have to
pass in a fresh recording.

## Draft it by clicking through

```bash
reshoot rec http://127.0.0.1:3000/ demo/draft.toml
```

This opens a fresh browser for you to do the task with demo data. Close it when
you finish, and it writes the clicks, typing and dropdown choices as beats.
Checkboxes and radio buttons record their chosen state. Multiple-choice lists,
file selection and drops leave a blocking `recording_issue` in that step,
preserving the rest of the draft for repair.

It also suggests result checks from what each action changed on the page:
the words you typed showing up in a list, a list getting shorter, a new
address, a label that changed. Each is marked
`# suggested from what this changed on the page`. Keep the ones that show the
result, delete the rest, and check counts that depend on data the app keeps.
The draft ends with the `end` beat the generated edit needs. Add captions and
purposes, give the beats better IDs than `action-1`, and use the draft to
replace `demo/storyboard.toml`. Every action and result check is in the
[project reference](projects.md#storyboardtoml).

## Login and demo data

Every take starts with a fresh browser profile, so reshoot never uses your own
browser's login. If the app needs one,
use a separate demo account and TOML `[[setup]]` actions before the recorded
beats. Setup actions use the same action fields, for example:

```toml
[[setup]]
type = "navigate"
url = "http://127.0.0.1:3000/demo-login"
```

That route is an example, not a feature reshoot adds. Implement an isolated
demo login or the app's actual test-account flow. Do not put real credentials
into a committed storyboard. If the login cannot be automated, solve that
before promising a recording CI can repeat. `blur = ["SELECTOR"]` can hide a
persistent demo header, but it is not a substitute for isolated data.

If fixture files live inside `demo/`, declare them with top-level
`inputs = ["seed.json"]` in `reshoot.toml`, before any table. Only existing files
inside that project directory are accepted. The report hashes declared inputs;
it does not capture an external database or service automatically.

## Record it

```bash
reshoot doctor --config demo/reshoot.toml
reshoot preview demo/reshoot.toml
reshoot run demo/reshoot.toml
```

Watch the preview before the final. A failing beat names its control; see
[Troubleshooting](troubleshooting.md#an-action-or-result-check-fails). Then
[accept the final](step-by-step.md#5-review-and-accept). For a portrait
export, choose a crop or record a separate mobile take: fitting a wide page
into a phone frame does not make its words readable.

When the app changes, keep the beat IDs and the result checks and record
again; [Keep a demo current](publish.md) covers comparing and sharing the new
run, and [Change and grow a demo](customize.md) covers captions, timing and
longer stories.
