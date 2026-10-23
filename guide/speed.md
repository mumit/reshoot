# Faster shoots

A shoot's time is mostly not the recording. Use this page to see where the time
goes, which settings shorten it, and what each one gives up. The settings are in
the [project reference](projects.md); this page is about choosing them.

## Where the time goes

A real example: an 81-second launch video with a 52-second web take, a Claude Code
terminal take and a one-window clip, all scanned at full frame rate.

| Step | Time |
|---|---|
| Web take | 2 min |
| Terminal take, an agent with a fixed 285 s `Sleep` | 6 min |
| Edit | 30 s |
| Full scan of the run: every frame, plus every image the page loaded | 17 min |
| Full scan of the finished files | 10 min |
| A preview before the final, with all of the above at lower resolution | 26 min |

The scans took about two-thirds of the final run. A full scan's time grows with the
number of frames (an 80-second video at 60 fps has about 4,800) and with every
image listed in a take's `.assets.json`. A page with a map loads hundreds of tiles.

## What to change

Each row is independent. Start at the top: those save the most.

| Change | How | Saves | Gives up |
|---|---|---|---|
| Sample the scan | Leave `full` out of `[check]`; set `every = SECONDS` (default 3) | Most of the scan on long videos | Something on screen for less than `every` seconds can be missed |
| Skip the scan | `scan = false` in `[check]`, or `reshoot check --no-scan` | All detection time | Only your eyes check the video |
| Scan fewer sources | Leave `takes/web.assets.json` out of `[check] sources` | Large on pages with maps, galleries or many images | Loaded images are seen only as they appear in frames, not at full size. Content picked at random goes unchecked |
| Preview less | Preview after changing the storyboard or a tape, not on every refresh | A whole extra run | A refresh that broke shows up in the final, which you then run again |
| Preview one beat | `reshoot preview CONFIG --from BEAT` | The beats before it | Skips the edit and scan, so it shows only that beat working |
| Re-cut, don't re-record | When only the edit changes (captions on cards, timing, GIF size), copy a run's `takes/` folder to a new folder and run `reshoot edit` there | Everything but the edit | The new cut is outside a versioned run: its report doesn't cover it |
| Tighten agent waits | Set a tape's final `Sleep` to the slowest run you've seen plus a margin | Minutes per terminal take | A slower agent is cut off before its answer. VHS can't safely wait for text instead ([pitfalls](pitfalls.md#terminal-takes)) |
| Export less | One MP4 and one GIF, not also a vertical cut and a GIF per section | Edit and scan time: each export is scanned | Less ready-made media for other places |
| Review less | Skip the review page and `reshoot check --ok` | Your time | The report stays "review pending". Nothing is blocked; sharing unreviewed media is your call |

Copy the takes before re-cutting because an edit writes beside its first take.
Run inside a run folder, it would overwrite that run's recorded files.

## When the fast settings are fine

Sampling or skipping the scan suits a refresh when:

- the demo data was checked and hasn't changed since;
- the app shows the same things each time, not a shuffle or "featured" picks;
- you watch the finished video once.

Keep the full scan when:

- the demo data is new or has changed;
- the app picks content at random, so this take may show something the last one didn't;
- the video is going somewhere public for the first time.

Whatever the settings, read anything an AI agent writes in a terminal take. It is
different every run, no earlier check covers it, and an agent's answer can describe
or name what it found.

## A quick refresh

For a project whose data has been checked, with one browser take:

```toml
[check]
sources = ["takes/demo-final.mp4"]
review = "review"
every = 3
```

```bash
reshoot run demo/reshoot.toml   # no preview: the storyboard hasn't changed
```

Then watch the MP4. Go back to the full settings when the data or the story changes.
