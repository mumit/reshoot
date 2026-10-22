# Make and maintain a demo

Use your coding agent to make a demo of one task in your app. Keep its actions,
captions, expected results and edit in a demo folder. When the app changes, ask
the agent to update the story and record it again.

## Start here

| Start with | Do this |
|---|---|
| App source code and a coding agent | [Paste the first-demo prompt](agent-quickstart.md) into a local session in the app repository |
| A running web app, without source code | Set the prompt's target to the URL; use the [running-app route](running-web-app.md) |
| An installed native app on a Mac | Set the prompt's target to the app and demo window; use the [window route](macos-window.md) |
| An existing reshoot demo | [Refresh or review it](agent-quickstart.md#update-the-demo-when-the-app-changes) with the previous run for comparison |
| A preference for the CLI, or no app yet | [Install the tools](install.md), then follow the [notes tutorial](step-by-step.md) |

The agent route handles setup and authoring with the
[create, refresh and review skills](../skills/README.md). The CLI tutorial
teaches the commands directly, using a bundled notes app. Both routes produce
a video and a README loop, retain recording attempts and leave acceptance to you.
Native capture uses a standalone recipe and app-specific interaction rather
than a browser storyboard.

## Build up at your own pace

| Stage | Get to | Agent route | Direct CLI route |
|---|---|---|---|
| 1. First success | One useful task, an MP4 and a GIF | [One prompt](agent-quickstart.md) | [Notes tutorial through the preview](step-by-step.md#2-record-a-preview), or a target route above |
| 2. Explore | Decide which features are worth adding | [Capabilities and examples](features.md) | The same feature guide, with source and command links |
| 3. Customize | Change words, timing and export size | [Ask for one visible change](customize.md) | Edit the generated files and record another preview |
| 4. Build a fuller story | A product demo or tutorial | [Expand a working clip](make-demo.md) | Author sections and edit takes |
| 5. Maintain and share | Updated media, reviewed before publication | [Refresh and prepare exports](publish.md) | Script the local run, then [add CI](ci.md) |

Stop after the first clip or skip to the stage you need. Reference reading and
CI setup are not prerequisites for trying reshoot.

## Find an answer

| Task | Guide |
|---|---|
| A first demo with a coding agent | [Agent quickstart](agent-quickstart.md) |
| Skill installation, invocation and capabilities | [Skill catalog](../skills/README.md) |
| Prerequisites, upgrades or a pinned installation | [Installation](install.md) |
| A first complete project | [Tutorial](step-by-step.md) |
| Available features and example source | [Feature guide](features.md) |
| Small changes to captions, timing and GIF size | [Customization](customize.md) |
| A fuller product demo or app tutorial | [Build a demo](make-demo.md) |
| Updates, selected exports and publication | [Maintain and publish](publish.md) |
| App startup, demo data, login or agent prompts | [Record your own app](your-app.md) |
| TOML actions, expectations, captions, edits and exports | [Project reference](projects.md) |
| A CLI command | [Command map](commands.md) |
| Help with a failed recording or pending review | [Troubleshooting](troubleshooting.md) |
| Python stories, VHS terminal takes or a macOS window | [Manual workflow](manual.md) |
| Automated recording on releases | [CI](ci.md) |
| Rendering and recording pitfalls | [Pitfalls](pitfalls.md) |

## The workflow

Choose one useful task and a visible result. Let the agent prepare synthetic
data and write the story, or author the files directly. Inspect a preview before
making a fresh final recording. Watch each finished export and review the
supplied images, frames and text findings.
Then copy selected files locally for sharing. Reshoot does not post automatically.

Versioned browser and terminal projects retain each candidate in `takes/runs/ID/`; a failed update
does not overwrite the previous recording. Choose the comparison baseline
explicitly and keep stable beat IDs so the old and new results can be compared.
Native window captures use separate take directories and manual comparison.

| Term | Meaning |
|---|---|
| Project | A brief, app setup, storyboard and edit configured by `reshoot.toml` |
| Run | One isolated attempt with its report, recordings and evidence |
| Take | One recording of a browser page, terminal or app window |
| Beat | A named step with actions, a caption, result checks and a hold |
| Storyboard | The beats in a TOML file, or a supported Python file |
| Tape | A [VHS](https://github.com/charmbracelet/vhs) script for a terminal take |
| Export | A finished MP4, GIF or other selected deliverable |
| Baseline | A previous run explicitly selected for comparison |
| Scan sheets | Numbered contact sheets and original frames for human inspection |

## When reshoot fits

Use reshoot for software demos that need updates: README loops, release
walkthroughs and feature clips. Scripting takes preparation, especially for
demo data. A one-off recording may be quicker with a single-window recorder.
Native desktop automation needs an app-specific way to drive the window;
reshoot's browser story format does not automate arbitrary desktop controls.

## Platforms

| Part | macOS | Linux | Windows |
|---|---|---|---|
| Browser stories and exports | CI, local and separate-Mac maintainer trials | CI and Debian 12 ARM64 Podman maintainer trials | Not validated |
| VHS terminal takes | Local promotional and notes workflows | Notes CI and full Podman promo build | Not validated |
| Native app window capture | One window by ID; local AppKit trial | Not supported | Not supported |
| Text scanning | Vision by default; Tesseract selectable | Tesseract | Not validated |
| Face and person detection | Vision; generated positive controls tested | Unavailable | Not validated |

The [Linux record](../docs/validation/2026-10-21-podman-linux.md),
[separate-Mac record](../docs/validation/2026-10-21-separate-mac.md) and
[Codex/Claude refresh and review record](../docs/validation/2026-10-22-separate-mac-harnesses.md)
describe the tested environments and their limits. Those are maintainer-operated
trials. Independent new-user testing is deferred; broader desktop, remote-service
and platform coverage remain open. These results establish behavior in the tested
environments, not compatibility with every app.

## Sound, captions and framing

Make the main point readable without sound. Captions, result holds and
deliberate framing matter more than motion for its own sake. Reshoot supports
zoom, styled captions, narration, music and subtitles; the
[project reference](projects.md) describes their settings. A portrait export
needs an intentional crop or a separately recorded responsive take.

The [manual workflow](manual.md) covers Python narration and custom edits.
The [promotional recipe](../examples/promo/README.md) demonstrates an authored
before-and-after video using real recordings of synthetic data.
