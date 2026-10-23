# Record a web app from source

For the shortest agent workflow, [paste the first-demo prompt](agent-quickstart.md)
into Codex or Claude Code in the app's repository. Let the agent handle setup
and authoring, then review its exports.

Use this walkthrough to write the files yourself or guide the agent's choices.
Choose one useful task in the app and keep the brief and recording source
beside its code. The [notes tutorial](step-by-step.md) provides a complete CLI
example to try separately; it is not a prerequisite for recording your app.

Use this route when you can read the web app's code and configure startup or
fixtures. If you only have a URL, use [the running-app guide](running-web-app.md).
For an installed desktop app, use [the macOS window guide](macos-window.md).
After the first clip, [customize its words and timing](customize.md), then
[build a fuller story](make-demo.md).

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

From the app repository's root:

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

Find targets in the app's source or browser inspector. An accessible role and
name work when they identify one control; a stable `data-testid` also works.
Use CSS when that is the clearest stable target. Reshoot fails on missing,
covered, disabled or ambiguous controls rather than forcing a click. Repair
the target or app state instead of removing the expected result.

To draft a story from recorded clicks, run:

```bash
reshoot rec http://127.0.0.1:3000/ demo/draft.toml
```

This opens a fresh browser profile for manual interaction. Use only demo data
and close that browser when finished. The draft still needs purposes, captions
and assertions. Inspect it before replacing the story. Some interactions,
including select, checkbox, radio and drop changes, are not supported by the
recorder and fail explicitly. Hand-authored TOML actions are listed in the
[project reference](projects.md#storyboards).

## Authentication and fixtures

Every take starts with a fresh browser profile. If the app needs authentication,
use a separate demo account and TOML `[[setup]]` actions before the recorded
beats. Setup actions use the same action fields, for example:

```toml
[[setup]]
type = "navigate"
url = "http://127.0.0.1:3000/demo-login"
```

That route is an example, not a feature reshoot adds. Implement an isolated
demo login or the app's actual test-account flow. Do not put real credentials
into a committed storyboard. `blur = ["SELECTOR"]` can hide a persistent demo
header, but it is not a substitute for isolated data.

If fixture files live inside `demo/`, declare them with top-level
`inputs = ["seed.json"]` in `reshoot.toml`, before any table. Only existing files
inside that project directory are accepted. The report hashes declared inputs;
it does not capture an external database or service automatically.

## Preview, finish and update

```bash
reshoot doctor --config demo/reshoot.toml
reshoot preview demo/reshoot.toml
reshoot run demo/reshoot.toml
```

Inspect the preview before the final run and follow the tutorial's
[review and export steps](step-by-step.md#4-accept-the-recording).
For full-frame final checks, set `full = true` in `[check]`. Choose a portrait
crop or record a separate mobile take; fitting a wide page into a phone
frame does not make its words readable.

When the app changes, keep the accepted run folder, retain stable beat IDs,
and record a new candidate. Repair selectors while keeping the task and its
proof intact, then compare the two explicit runs. Changed mock data, claims,
speed or narration deserve their own explanation in the brief.

## Use an agent

Use the [agent quickstart](agent-quickstart.md) for setup and a first demo in
one conversation. The examples below specify the task and run IDs explicitly
when working with an existing setup.

To use this workflow with an agent, install the bundle for your harness from
the app repository's root:

```bash
reshoot skills codex --directory .
```

Or, for Claude Code:

```bash
reshoot skills claude --directory .
```

Start a conversation in that project and invoke the skill with a concrete
task. For Codex:

```text
$reshoot-demo
Use or create the demo/ project for the local app at http://127.0.0.1:3000/.
Use its isolated synthetic fixture data. Show saving a task and finding it by
search. Read the app code to choose controls and explicit result checks.
Produce a README GIF and an MP4 with captions. Inspect a preview before the
fresh final and report the output paths and review instructions.
```

For Claude Code, use `/reshoot-demo` followed by the same task. With the plugin,
use `/reshoot:reshoot-demo`. Choose the project-local skills or the plugin for
the project. Both routes need the [CLI and recording tools](install.md).

For an update, use this Codex prompt. `demo/accepted` names the newest run you
accepted. In Claude Code, replace the first line with `/reshoot-refresh`:

```text
$reshoot-refresh
Refresh demo/reshoot.toml against demo/accepted, using its exact run ID.
The app's search field changed. Keep the same task, beat IDs and result checks;
repair the target if needed. Retain failed attempts and the previous recording.
Inspect a repaired preview, make a fresh final and compare both runs.
Report the final MP4/GIF paths and any unresolved review items.
```

For review, use this prompt. `demo/latest` names the newest successful run.
In Claude Code, replace the first line with `/reshoot-review`:

```text
$reshoot-review
Review demo/latest against demo/accepted.
Read the existing reports and inspect the actual MP4, GIF and beat evidence.
Explain scan coverage, findings and which human decisions remain pending.
Preserve existing recordings and review evidence; report whether a new check is needed.
```

Include the task after the skill invocation so the agent knows which recording
to inspect. A new conversation does not imply it has forgotten project
instructions or account-level memory.

Plugin installations use `/reshoot:reshoot-refresh` and `/reshoot:reshoot-review`
for those two tasks. The marketplace installation follows Claude's
[plugin instructions](https://code.claude.com/docs/en/discover-plugins).

The agent can prepare, run and inspect the demo. Watch the final exports and
make the recording and scan-sheet decisions before sharing.
