# Share reshoot

Use these descriptions and draft posts to introduce reshoot. Link to the
repository, where the first-demo prompt is the primary next step. Attach the
accepted promotional video when preparing a post. Publish only with the owner's
authorization.

## Describe the project

**Short description:** Agent skills and recording tools for repeatable software
demo videos.

**Headline:** Give your agent a task. Get a demo you can run again.

**One paragraph:** Use reshoot with Codex or Claude Code to turn a task in a web
app into a captioned MP4 and a README GIF. The agent reads the app, writes a
checked story and records the workflow. Keep the recording source beside the
code, then use the refresh skill after the UI changes. Watch and review the
exports before sharing. Reshoot is open source under the MIT license.

## Draft for X

```text
Your coding agent can make the demo, too.

reshoot gives Codex and Claude Code skills to create, refresh and review demo
videos. Get an MP4, a README GIF, and source to record again after UI changes.

Start with one prompt:
https://github.com/mumit/reshoot
```

Attach the accepted social MP4 at `docs/demo/reshoot.mp4`. The existing video
shows the app changing and the same task running in both versions. Keep that
visible before-and-after result in the post; it demonstrates the repeatability
claim. The clip is an authored edit with generation waiting omitted and labeled.

## Draft for LinkedIn

```text
The app changed. The demo can change with it.

reshoot is an open source toolkit that gives Codex and Claude Code a workflow
for making software demo videos.

Open your app's repository, paste the first-demo prompt, and let the agent
prepare a short captioned MP4 and a README GIF. It reads the app, uses synthetic
demo data, writes actions with expected results, and inspects a preview before
recording a fresh final.

Keep the recording source beside the code. When the UI changes, use the refresh
skill to record the same task again and compare it with the previous version.
Use the review skill to inspect the outputs and report remaining decisions.

You watch the exports and decide what to share.

The clip shows the same notes task before and after a UI change. Setup details
depend on the app; recording tools and an isolated demo login may need setup.

Start with the copyable prompt in the README:
https://github.com/mumit/reshoot
```

## Match the next step to the reader

| Reader | Invitation | Destination |
|---|---|---|
| New to recording tools, already uses a coding agent | Open the app repository and paste one prompt | [First-demo prompt](../guide/agent-quickstart.md#start-with-one-prompt) |
| Already uses agent skills | Install the package, then invoke create, refresh or review with a task | [Skill catalog](../skills/README.md) |
| Wants control over every action | Author the story and run the tools directly | [CLI tutorial](../guide/step-by-step.md) and [own-app walkthrough](../guide/your-app.md) |
| Maintains release automation | Record candidates in CI and review the artifacts | [CI guide](../guide/ci.md) |

Lead with the visible result, then explain the repeatable source and three
skills. Keep installation choices behind the first-demo prompt. Use concrete
examples: save and find a task, create and label an issue, or filter a set of
synthetic search results.

Describe the agent's work separately from the CLI's capabilities. The agent
chooses and repairs the story; the CLI records configured actions, checks
expected results, edits media and retains evidence. Keep setup-time and
time-saving claims tied to measured evidence. Independent new-user testing
remains deferred; the current trials were maintainer-operated.
