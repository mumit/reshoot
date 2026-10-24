# Persona review of the docs

On 2026-10-23, after 0.3.3, five fresh agent sessions read the docs as five
kinds of user and reported what helped, what hurt and what they would change.
One also ran the CLI tutorial end to end in an empty folder. The others only
read the docs, the help text and the code. The maintainer checked the main
claims against the code before writing this record.

| Persona | Read | Score |
|---|---|---|
| A developer who has never made a demo video | README, install, the tutorial, run by hand | 7: "would recommend after 15 minutes" |
| A product-video professional | README, features, customize, make-demo, publish, speed, manual, the promo | 6: "credible and fun" |
| An engineer who lives in Claude Code or Codex | README, agent quickstart, skills, CI, the cold-run record | 7: "feels like magic, and I trust it" |
| An engineering lead adopting it for a team | All guides, `--help`, the workflows, the action | 6: "would adopt for my team" |
| A visitor with five minutes | README and the hero media | 6: "would try it today" |

## What works

- **The output.** The tutorial's first preview took 13 seconds after two
  commands and gave a clean captioned GIF. The hero GIF explains re-recording in
  ten seconds.
- **Failures.** A broken selector names the beat, the target and the count,
  and the fix is one line. The Chrome and port errors point at their causes.
- **Trust.** Hash-bound acceptance, runs that never overwrite each other,
  pinned actions, masked secrets and no automatic publishing all read as the
  right design to the team lead.
- **Craft under the hood.** The spring-damped zoom with anticipation, audio
  ducking, CRF 17 at 60 fps and per-GIF palettes impressed the video
  professional, who had to find them in the code.

## What hurts

### The finish line

Every run ends with a warning instead of the result.

- `reshoot run` prints the report path, "Human review is pending" and the
  accept command (`run.py:280-291`). It never prints the GIF's path, and prints
  the MP4's only under `== edit`. "Three passed expectations" is not shown.
- The app server's request log, including a favicon 404, is mixed into the
  output.
- A failed preview prints no run folder or failure image, though the tutorial
  says to keep both.
- `reshoot compare --out` prints nothing.
- `review.html` opens with raw JSON before any human status line.
- The tutorial makes the reader paste run IDs three times
  (`step-by-step.md:68,116,246`) although `latest` and `accepted` exist.
- Turning on `full = true` in step 3 is never undone, so later previews scan
  373 items instead of 6 and take 2.5 times as long. The CLI then asks for 390
  items to be looked at "at full size", which reads as homework for made-up
  data.

### The front door

- The README never says `uv tool install 'reshoot[browser]'`, so a PyPI
  visitor isn't shown how to install it.
- The first call to action is a 12-line prompt; the CLI's four lines are near
  line 180.
- The hero's line, "Your app changed. Your demo can too.", is stronger than any
  sentence in the README, and no storyboard is ever shown.
- Requirements are spread over three places. "Three skills" is followed by
  "all ten skills". Four tables answer "where do I go next".
- There is no "how is this different from VHS, Screen Studio or Playwright
  video".
- The prose reads as governance more than creative tooling: "approval",
  "verdict", "not validated", "execution success is not approval to publish".

### The agent handoff

- Nothing a human reads gives the time (2 to 9 minutes) or the cost (about $1),
  says that skills are written into `.claude/skills/` or `.agents/skills/`, or
  warns Codex users that Chrome must run outside the sandbox.
- The handoff has no fixed shape: no "reply accept, or ask for changes like
  these", no follow-up prompts for shorter captions, slower pacing, a portrait
  cut, a voiceover or CI setup.
- The first demo never exports to a stable path, but the CI template expects
  `docs/demo/demo-final-readme.gif`. Nothing ignores `demo/takes/`, and agents
  are told not to edit `.gitignore`.
- The quickstart says to install the skills after an upgrade, and also to keep
  existing ones, and the installer won't overwrite them. After an upgrade the
  old skills stay.
- The skills still hedge with "if this CLI provides `reshoot review`" although
  they require 0.3.2.

### Accuracy

Checked against the code:

- `guide/ci.md:22` says `reshoot accept demo/latest`. `latest` is the newest
  successful run, previews included (`review.py:13`), and `accept` does not
  refuse a preview, so a team can commit a preview as its CI baseline.
- `guide/your-app.md:145` and `guide/pitfalls.md:106` say there is no `select`
  action; 0.3.2 added it.
- `guide/projects.md:68` says the skills need CLI 0.2; they need 0.3.2.
- `guide/publish.md:7-30` still describes archiving an accepted run by ID,
  before `demo/accepted/` existed.
- `reshoot run --help` describes only the legacy format. `doctor`, `init`,
  `preview`, `edit`, `gif` and `last-change` have no help text.
- `pitfalls.md:58-59` says a higher pixel ratio does not sharpen video, while
  `zoom.py:7` and the record-web skill say it keeps zoomed text sharp.

### Craft

- TOML storyboards, the recommended route, move the cursor with easing but
  have no click ripple or press, and type at a flat 65 ms per character
  (`browser.py:48-55`). The Python route has all three (`overlay.js`).
- There is no picture of zoom, the cursor, caption styles, cards or aspect
  ratios anywhere in the docs. The best account of the camera is a list of
  fixed bugs in the pitfalls page.
- No browser background, padding, rounded corners or shadow, the look
  professionals expect from Screen Studio.
- No platform presets with numbers. Caption and card styling are half a
  sentence in a reference paragraph.
- Words differ from the trade: storyboard for script, beat for shot, card for
  title card. Ducking and auto-zoom are never named.

### Structure

- Seventeen guide pages overlap: install steps appear four times, skill
  installation five, the accept flow four.
- No start-here for a team lead or a pull-request reviewer, and no page on
  adopting reshoot as a team: who owns `demo/accepted/`, branch protection,
  telling someone when the refresh fails, CI cost.
- Terms vary: run, take, shoot, candidate, attempt and recording; result check,
  expectation and assertion; accept and approve; baseline, accepted, previous
  and record.
- No index of error messages in the troubleshooting guide.

## What the maintainer takes from it

The tool already does the hard part. What a user meets first, the README, the
end of a run and the agent's handoff, is where the joy is lost. The roadmap now
leads with making reshoot a joy to use, ordered by how early a user meets each
problem.

## Limits

- The personas were agents playing users, not people. Their scores show
  direction, not measurement.
- Only the first-timer ran anything. The CI and team claims come from reading.
- No GUI was available, so `review.html` was judged from its source.
