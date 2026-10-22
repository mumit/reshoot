# Build a product demo or tutorial

Start from a working short recording. Expand it when each extra section helps
the audience understand the product or complete a task. Use the same workflow
for your own app or an existing app you can operate with demo data.

## Choose the promise

Write the audience, starting state and visible result in `BRIEF.md`. Decide
whether to show why a feature matters or how to use it. For a product demo,
lead with the result and keep setup short. For a tutorial, include the steps a
viewer must repeat and hold menus and result text long enough to read.

For example, build a notes tutorial around one outcome:

| Section | Show | Proof |
|---|---|---|
| Start | A list with several demo notes | The target is hard to spot |
| Create | Add “Prepare the release notes” | The saved note appears |
| Find | Search for “release” | Only the matching note remains |
| Finish | Hold the result and explain the next action | The result stays readable |

Keep each section small enough to rerecord on its own. For browser stories,
use stable beat IDs and assertions for saved state and filtered results.
For native apps, save the starting document and automation or manual steps;
check the visible result yourself. Do not claim automated native assertions.

## Ask the agent to build from the working clip

```text
Expand the existing demo/ into a short tutorial of creating an item and finding
it by search. Read its brief and current recording first. Use synthetic data.
Keep the working task and result checks; add only the context needed to follow
it. Use clear captions, readable result holds and a short closing instruction.
Keep source files editable. Inspect previews, record a fresh final, and show
the MP4 and README GIF with unresolved review items.
```

Add the intended audience, destination and length when known. Ask for narration
only when it adds explanation; the video should still make sense muted.

## Assemble the story with the CLI

Edit the storyboard first, then use `reshoot preview demo/reshoot.toml` to
check the complete task. Use `demo/edit.toml` to select beat ranges, combine
takes and add cards. This complete edit adds a short title to the notes project:

```toml
schema_version = 1
output = "demo-final.mp4"

[[part]]
card = "Save a note. Find it again."
duration = 1.5

[[part]]
take = 0
start = 0
end = "end"

[[export]]
name = "readme"
format = "gif"
width = 800
height = 450
```

Replace the notes project's edit with this file and record another preview.
For a different story, use its actual beat names. Keep the proof and enough
reading time in every shortened export. Use numeric cuts for native takes.

Use [declarative edits and exports](projects.md#edit-and-export) for additional
sections and destinations. Use the [manual workflow](manual.md) for Python
editing, narration and VHS terminal segments. Match terminal and browser take
dimensions when combining them. The [notes source](../examples/notes/)
demonstrates these pieces; the [promo recipe](../examples/promo/README.md)
shows a before-and-after video assembled from real synthetic-app recordings.

## Finish for the viewer

Watch the full MP4 and every shorter GIF or crop. Check that captions name the
outcome, text fits, typing is legible and the result remains on screen.
Identify mocked responses and shortened waits. Check narration against the
picture and inspect the subtitle text when present.

Make a fresh final after the preview works. Review its recording and scan
sheets separately. Keep the source and the accepted take together so the next
update preserves the same story.

Next: [maintain, publish and automate the demo](publish.md).
