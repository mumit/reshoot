# Choose what to add next

Start with one task and a visible result. Watch the
[21-second before-and-after demo](../docs/demo/reshoot.mp4), then choose the
capability that helps your audience. Add one feature at a time so you can judge
whether it improves the recording.

| Goal | Use | Try next |
|---|---|---|
| Get a first clip of your app | Agent chooses actions and checks, CLI records and exports | [First-demo prompt](agent-quickstart.md) |
| Explain a task without sound | Short captions and readable result holds | [Customize a caption and timing](customize.md) |
| Draw attention to a control | Browser cursor, typing, click zoom and caption placement | [Browser settings](projects.md#storyboards) |
| Show a CLI alongside the UI | VHS terminal take, edited with the browser take | [Notes source](../examples/notes/) and [manual workflow](manual.md) |
| Show an installed native app | One macOS window by ID | [Window workflow](macos-window.md) |
| Explain a longer process | Named sections, title cards, narration and subtitles | [Build a demo or tutorial](make-demo.md) |
| Make a README loop or social clip | GIF and MP4 export profiles; intentional framing | [Edits and exports](projects.md#edit-and-export) |
| Update a demo after a UI change | Saved task, explicit expected results, new run, old/new comparison | [Maintain and publish](publish.md) |
| Record candidates after commits or releases | Versioned project in GitHub Actions | [CI setup](ci.md) |

## Know what needs preparation

Browser recording runs on macOS or Linux and works with source code or just a
reachable URL. Prepare isolated demo data and authentication that work in a
fresh browser profile. Writing the first story takes more work than replaying
it. An agent can inspect code or the page to choose targets; it still needs a
working app and an observable result.

Native window recording is macOS-only. Save an app-specific automation script
for repeatable interaction, or perform the task yourself during capture.
Browser captions, click zoom and assertions do not carry over to native input.
See [platforms and tested limits](README.md#platforms) before choosing a route.

Checks report execution, expected results and scanning separately. They help
find problems; they do not replace watching the exports and reviewing scan
sheets. Publication stays under your control.

## Explore the source when ready

Use [customization](customize.md) for small edits to the files generated in
`demo/`. Use the [notes example](../examples/notes/) to explore Python
stories, terminal takes, narration and custom cuts. Use the
[promotional recipe](../examples/promo/README.md) for a complete authored
before-and-after piece. The [project reference](projects.md) and
[command map](commands.md) provide the exact settings and commands.
