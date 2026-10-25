# Skills for repeatable demo videos

Give a coding agent the workflow for making a demo, updating it when the app
changes, and checking the result before sharing. Reshoot's skills guide the
agent through the work; the reshoot CLI records and edits the media.

A skill is instructions, not a program. It needs a coding agent, a harness such
as Claude Code or Codex with its model, to read it and run the commands. The
CLI on its own needs neither; see
[What your agent needs](../guide/agent-quickstart.md#what-your-agent-needs).

For a first video, use the [agent quickstart](../guide/agent-quickstart.md).
Paste its prompt into Codex or Claude Code in your app repository or a demo work
folder and let the agent handle setup. Supply source code, a running URL or an
installed macOS app with a demo window. Source code is optional.

## Start with three skills

| Skill | Use it to | Supply |
|---|---|---|
| [reshoot-demo](reshoot-demo/SKILL.md) | Choose the capture route, make a first clip, inspect a test take and prepare final exports | App source, a web URL or a native macOS app; the task to show |
| [reshoot-refresh](reshoot-refresh/SKILL.md) | Record an existing task again after an app change and compare the result | Configuration and exact previous run, or native recipe and previous media |
| [reshoot-review](reshoot-review/SKILL.md) | Inspect exports, result checks, readability, scan coverage and comparisons | Current and optional previous run, or standalone media and check reports |

Invoke the skill with the task in the same message. For example, in Codex:

```text
$reshoot-demo
Show adding an issue and finding it by its label. Use synthetic demo data.
Create a short captioned MP4 and a README GIF for this app.
```

In Claude Code, use `/reshoot-demo`. For the plugin, use
`/reshoot:reshoot-demo`. Apply the same prefix convention to refresh and review.

## Install the package

Install the [CLI and platform dependencies](../guide/install.md), then choose
one route:

| Route | Installation | Included skills |
|---|---|---|
| Codex, project-local | Run `reshoot skills codex --directory .` in the app or demo folder | Three primary skills in `.agents/skills/` |
| Claude Code, project-local | Run `reshoot skills claude --directory .` in the app or demo folder | Three primary skills in `.claude/skills/` |
| Claude Code plugin | Run the two commands below inside Claude Code | All ten skills |

```text
/plugin marketplace add mumit/reshoot
/plugin install reshoot@reshoot
```

Follow Claude Code's installation and reload prompts. The plugin uses namespaced
invocations such as `/reshoot:reshoot-demo`. The skills need the CLI and recording
tools for every route. See [setup and discovery](../guide/agent-quickstart.md#install-the-skills-yourself).

The CLI bundles the same primary skill source used by the plugin. It refuses
to overwrite existing project skills. Upgrading the CLI does not update those
copies; preserve local edits and compare a new bundle before replacing them.

## Use the supporting skills

The plugin also includes focused workflows for individual parts of a shoot:

| Skill | Purpose |
|---|---|
| [plan-demo](plan-demo/SKILL.md) | Choose the story, result, captions and recording format |
| [record-web](record-web/SKILL.md) | Record a browser page from a storyboard |
| [record-terminal](record-terminal/SKILL.md) | Record a CLI or agent with VHS |
| [record-window](record-window/SKILL.md) | Record one macOS app window |
| [check-privacy](check-privacy/SKILL.md) | Generate and inspect scan sheets and findings |
| [cut-video](cut-video/SKILL.md) | Edit takes and produce finished exports |
| [keep-current](keep-current/SKILL.md) | Run a shoot from configuration or prepare CI recording |

Use the primary skills for a complete first demo or update. Use a supporting
skill when working on that part separately. The three-skill CLI installer does
not install these seven supporting skills.

The three primary skills cover all three starting points without requiring the
supporting bundle. Browser stories support captions and explicit result checks.
Native takes require app-specific automation or manual interaction, standalone
editing and manual comparison; browser overlays and result checks do not apply.

After the first clip, see [how the videos look](../guide/look.md),
[change and grow the demo](../guide/customize.md) or
[keep it current and share it](../guide/publish.md).

## Keep the review with the recording

The agent can prepare a story, run commands, inspect outputs and explain
findings. The owner watches the final exports and decides whether the recording
and scan sheets are acceptable. A successful command or clean scan does not
make that decision.

Use synthetic demo data and page, terminal or single-window capture. Retain
the previous run for a refresh. Keep publication and repository changes within
the owner's authorization.

## Extend a workflow

Keep shared skill source in this directory. The wheel packages it and the CLI
copies the primary skills into each harness's project location. Follow the
[contribution guide](../CONTRIBUTING.md#add-a-skill) when adding a skill or fixing
a recording pitfall.
