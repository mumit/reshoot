"""reshoot: demo videos of software, made from scripts so you can shoot them again when the app changes."""
import argparse, sys, textwrap


class Examples(argparse.HelpFormatter):
    """Wraps a description's prose and keeps its indented examples as they are."""
    def _fill_text(self, text, width, indent):
        return '\n\n'.join(part if part.startswith('    ') else textwrap.fill(part, min(width, 110))
                             for part in text.split('\n\n'))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reshoot", description=__doc__)
    from importlib.metadata import version
    ap.add_argument("--version", action="version", version=version("reshoot"))
    sub = ap.add_subparsers(dest="cmd", required=True)

    from reshoot import web, window, check, story
    p = sub.add_parser("web", help="record a web page acting out a storyboard, in headless Chrome",
                       description=story.__doc__ + "\nLegacy Python storyboards\n\n" + web.__doc__,
                       formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("storyboard", help="a storyboard.toml, or a legacy Python storyboard")
    p.add_argument("out", help="the video to write, such as takes/web.mp4")
    p.add_argument("--url", help="the page to open (default: the storyboard's URL)")
    p.add_argument("--size", help="CSS width x height @ device pixel ratio, such as 390x844@3 (default 1280x720@1.5)")
    p.add_argument("--theme", choices=["dark", "light"])
    p.add_argument("--mobile", action="store_true", help="a phone: touch and a mobile viewport")
    p.add_argument("--from-beat", help="replay earlier beats without recording them")
    p.add_argument("--zoom", nargs="?", type=float, const=True, metavar="SCALE",
                   help="zoom in on clicks and typing, enlarging up to SCALE (default 1.8)")
    p.set_defaults(run=web.main)

    p = sub.add_parser("window", help="record one app window on macOS, never the whole screen",
                       description=window.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("app", nargs="?", help="the app's name, as `--list` shows it")
    p.add_argument("out", nargs="?", help="the .mov to write")
    p.add_argument("-s", "--seconds", type=int, default=8, help="how long to record (default 8)")
    p.add_argument("--title", help="only a window whose title contains this")
    p.add_argument("--id", type=int, help="a window id from --list, if the app has several windows")
    p.add_argument("--list", action="store_true", help="list the windows on screen")
    p.set_defaults(run=window.main)

    p = sub.add_parser("check", help="put everything a take could show on sheets, to check by eye",
                       description=check.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sources", nargs="*", help="images, folders, URLs, .assets.json lists or videos")
    p.add_argument("--review", default="review", help="the folder for sheets and the list of what passed")
    p.add_argument("--every", type=float, default=3, help="seconds between frames taken from a video")
    p.add_argument("--full", action="store_true", help="inspect every decoded video or GIF frame")
    p.add_argument("--fail", nargs="+", metavar="LABEL", help="these failed")
    p.add_argument("--ok", action="store_true", help="every other image on the sheets passed")
    p.add_argument("--watch-for", action="append", metavar="WORDS",
                   help="words to flag wherever they appear, comma-separated, or @FILE with one per line")
    p.add_argument("--text-file", action="append", default=[], help="scan exact .srt, .voice.json, screenshots.json or tours.json text")
    p.add_argument("--ocr", choices=["auto", "vision", "tesseract"], help="explicit OCR backend; failures never silently fall back")
    p.add_argument("--no-scan", dest="scan", action="store_false", help="don't scan for likely problems")
    p.set_defaults(run=check.main)

    from reshoot import cut
    p = sub.add_parser("gif", help="a GIF of part of a take, between two beats or times",
                       description="Make a GIF of part of a take, with its own palette.\n\n"
                       "    reshoot gif takes/web.mp4 takes/loop.gif search end\n"
                       "    reshoot gif takes/web.mp4 takes/loop.gif 2.5 9\n\n"
                       "Beat names come from TAKE.beats.json, which `reshoot web` writes beside the video. For a "
                       "project's exports, use an [[export]] with format = \"gif\" in edit.toml instead.", formatter_class=Examples)
    p.add_argument("take", help="the video, such as takes/web.mp4"); p.add_argument("out", help="the GIF to write")
    p.add_argument("start", help="a beat name from TAKE.beats.json, or seconds")
    p.add_argument("end", nargs="?", help="a beat name or seconds (default: the end of the take)")
    p.add_argument("--fps", type=int, default=15, help="frames a second (default 15)")
    p.add_argument("--width", type=int, default=800, help="width in pixels (default 800)")
    p.set_defaults(run=cut.gifs_main)

    p = sub.add_parser("last-change", help="when a take last changed, such as when a command in a terminal finished",
                       description="Print the time in seconds of the last visible change in a video. For a terminal "
                       "take recorded with a long fixed Sleep, that is about when the command finished, so an edit "
                       "can cut there: reshoot last-change takes/cli.mp4", formatter_class=Examples)
    p.add_argument("take", help="the video to look at")
    p.set_defaults(run=lambda a: print(f"{cut.last_change(a.take):.2f}"))

    from reshoot import rec
    p = sub.add_parser("rec", help="write a storyboard by clicking and typing through the app in Chrome",
                       description=rec.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url", help="the page to start on, such as http://127.0.0.1:3000/")
    p.add_argument("out", help="the storyboard to write: demo/draft.toml, or a .py file for the legacy format")
    p.add_argument("--size", default="1280x720@1.5", help="the page size the storyboard is for (default 1280x720@1.5)")
    p.add_argument("--headless", action="store_true", help=argparse.SUPPRESS)
    p.set_defaults(run=rec.main)

    from reshoot import repair
    p = sub.add_parser('repair', help='inspect a missing control and explicitly choose its replacement',
                       description='Inspect a failed browser run. --apply rechecks a suggested control in the current '
                       'app before changing the target; --pick replays to the broken step and opens a fresh browser '
                       'where you select and confirm the replacement. The app action is not activated by selection. '
                       'Operation types and expected result values stay unchanged. Record a new preview afterwards.\n\n'
                       '    reshoot repair demo/takes/runs/ID\n'
                       '    reshoot repair demo/takes/runs/ID --apply\n'
                       '    reshoot repair demo/takes/runs/ID --pick', formatter_class=Examples)
    p.add_argument('run_path', help='the failed run printed by preview or run')
    p.add_argument('--config', help='the project reshoot.toml (default: beside the run folder)')
    choice = p.add_mutually_exclusive_group()
    choice.add_argument('--apply', action='store_true', help='revalidate and apply the suggested control')
    choice.add_argument('--pick', action='store_true', help='select and confirm the replacement in the app')
    p.add_argument('--headless', action='store_true', help=argparse.SUPPRESS)
    p.set_defaults(run=repair.main)

    from reshoot import run
    p = sub.add_parser("run", help="run a whole shoot from a reshoot.toml: the app, every take, the cut and the check",
                       description=run.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("config", nargs="?", default="reshoot.toml", help="the project's reshoot.toml (default: here)")
    p.add_argument("--full", action="store_true",
                   help="scan every frame of the exports this time, as full = true in [check] does")
    p.set_defaults(run=run.main)

    p = sub.add_parser("recut", help="edit an earlier run's takes again, with the captions as they are now, without recording",
                       description="Edit and scan an earlier run's takes again, into a new run, without starting "
                       "the app or recording: for a change to edit.toml, such as title cards, music, a frame or the "
                       "exports, or to a caption's words or the storyboard's [caption] look, which are drawn again. The "
                       "new run keeps that recording's result checks and names the run it came from.\n\n"
                       "    reshoot recut demo/latest\n"
                       "    reshoot recut demo/takes/runs/ID --full", formatter_class=Examples)
    p.add_argument("run_path", metavar="RUN", help="the run whose takes to use, such as demo/latest")
    p.add_argument("--config", help="the project's reshoot.toml (default: the one beside the run's takes folder)")
    p.add_argument("--full", action="store_true", help="scan every frame of the exports this time")
    p.set_defaults(run=run.recut)

    p = sub.add_parser("edit", help="cut takes into the final video and its exports, from an edit.toml or a Python script",
                       description="Cut takes into a final video and its exports. A run does this itself from "
                       "[edit] in reshoot.toml; use this to edit takes you recorded separately.\n\n"
                       "    reshoot edit edit.toml takes/web.mp4              # take 0 is takes/web.mp4\n"
                       "    reshoot edit edit.py takes/web.mp4 takes/cli.mp4  # a script using reshoot.cut\n\n"
                       "An edit.toml lists [[part]] ranges by take index and beat name, title cards, music, and "
                       "[[export]] profiles; guide/projects.md has every field. A .py script gets the other "
                       "arguments in sys.argv.", formatter_class=Examples)
    p.add_argument("script", help="an edit.toml, or a Python script that uses reshoot.cut")
    p.add_argument("args", nargs=argparse.REMAINDER, help="the takes, in the order the edit numbers them")
    p.set_defaults(run=run_script)

    from reshoot import project
    from reshoot import create
    p = sub.add_parser('create', help='make a demo by showing a task, then shape its preview in the studio',
                       description='Create a project, check the tools, open a fresh browser to record your task, '
                       'then make a preview and open the studio. Use the recording toolbar to add captions and '
                       'result checks, pause, hide an element and finish. Use demo data. Without a URL, try the '
                       'bundled notes app. Nothing is accepted or published.\n\n'
                       '    reshoot create\n'
                       '    reshoot create http://127.0.0.1:3000/ --directory demo', formatter_class=Examples)
    p.add_argument('url', nargs='?', help='your demo app URL; omit to try the bundled notes app')
    p.add_argument('--directory', default='demo', help='a new project folder (default: demo; existing projects are kept)')
    p.add_argument('--size', default='960x540@1.5', help='recording viewport (default: 960x540@1.5)')
    p.add_argument('--no-open', action='store_true', help='print the studio address instead of opening its page')
    p.add_argument('--no-studio', action='store_true', help='finish after the preview; open the studio later')
    p.set_defaults(run=create.main)
    p = sub.add_parser('doctor', help='check that the tools a project needs are installed, without recording',
                       description='Check that ffmpeg, Chrome, Playwright, VHS and the scan detectors a project needs '
                       'are installed, and say whether a newer reshoot is out. It does not record or run a scan, so '
                       'a run can still fail. Exits 0 when everything needed is there and 2 when something is missing.'
                       '\n\n    reshoot doctor --config demo/reshoot.toml', formatter_class=Examples)
    p.add_argument('--config', help='the project to check for; without it, the tools for a browser take')
    p.add_argument('--json', action='store_true', help='print paths, versions and detectors as JSON')
    p.set_defaults(run=project.doctor)
    p = sub.add_parser('init', help='create a demo project: the made-up notes example, or a draft for your app',
                       description='Create a demo project: BRIEF.md, storyboard.toml, edit.toml, reshoot.toml and a '
                       '.gitignore that keeps recordings out of git.\n\n'
                       '    reshoot init demo                                 # the notes example, ready to record\n'
                       '    reshoot init demo --url http://127.0.0.1:3000/    # a draft story for your app\n\n'
                       'The notes example includes its own small app on a free port. A --url draft has one '
                       'placeholder beat to replace with your app\'s task. It refuses to overwrite existing files.',
                       formatter_class=Examples)
    p.add_argument('directory', nargs='?', default='.', help='the folder to create, such as demo (default: here)')
    p.add_argument('--url', help='your demo app; omit to use the made-up notes example')
    p.set_defaults(run=project.init)
    p = sub.add_parser('preview', help='record a quick, smaller run with the same actions, to look at before a final',
                       description='Record a preview: the same actions and result checks as a final, at a smaller '
                       'size with faster encoding and a sampled scan. It gets its own run folder and cannot be '
                       'accepted without --preview, so record a final with `reshoot run` once it looks right.\n\n'
                       '    reshoot preview demo/reshoot.toml\n'
                       '    reshoot preview demo/reshoot.toml --from search   # record from the search beat on',
                       formatter_class=Examples)
    p.add_argument('config', nargs='?', default='reshoot.toml', help="the project's reshoot.toml (default: here)")
    p.add_argument('--from', dest='from_beat', metavar='BEAT',
                   help='replay setup and earlier beats without recording them, then record from BEAT; skips the edit '
                   'and scan')
    p.set_defaults(run=run.preview)
    from reshoot import skills
    p = sub.add_parser('skills', help='install the reshoot-demo, reshoot-refresh and reshoot-review skills in a project',
                       description='Copy the three main skills, reshoot-demo, reshoot-refresh and reshoot-review, '
                       'into a project: .agents/skills for Codex or .claude/skills for Claude Code. They match this '
                       'version of reshoot, so after an upgrade run it again with --replace. The Claude Code plugin '
                       'has these and seven supporting skills.\n\n    reshoot skills claude --directory .',
                       formatter_class=Examples)
    p.add_argument('harness', choices=['codex', 'claude'], help='the agent that will use them')
    p.add_argument('--directory', default='.', help='project root receiving the skill bundle')
    p.add_argument('--replace', action='store_true',
                   help='replace skills already there, such as after an upgrade; changes made to them are lost')
    p.set_defaults(run=skills.install)
    from reshoot import review
    runs = ('A run is its folder, such as demo/takes/runs/ID. End the path with `latest` for the newest successful '
            'run or `accepted` for the newest accepted one, such as demo/latest.')
    p = sub.add_parser('runs', help='list a project\'s runs, newest first, with their result and review status',
                       description='List the runs of a versioned project, newest first. ' + runs)
    p.add_argument('project', nargs='?', default='.', help='the project folder or its reshoot.toml (default: here)')
    p.set_defaults(run=review.listing)
    p = sub.add_parser('compare', help='compare matching beat IDs between two explicit runs',
                       description='Compare two runs beat by beat: which beat IDs match, and whether each beat\'s '
                       'definition, duration, evidence frame and results changed. A matched ID does not mean equal '
                       'pixels. ' + runs)
    p.add_argument('previous', help='the earlier run, usually the accepted one')
    p.add_argument('current', help='the run to compare against it')
    p.add_argument('--out', help='write the comparison JSON here instead of printing it')
    p.add_argument('--markdown', metavar='FILE', help='also write a short Markdown summary, such as for a pull request')
    p.set_defaults(run=lambda a: (review.compare(a), 0)[1])
    p = sub.add_parser('review', help='create a local review page or import owner decisions',
                       description='Write RUN/review.html: the exports, each beat\'s result and evidence, and the scan '
                       'items, with a comparison when --previous is given. Runs write this page themselves; use this to '
                       'add a comparison or rebuild it. ' + runs)
    p.add_argument('run_path', help='the run to review')
    p.add_argument('--previous', help='an earlier run to compare against, usually the accepted one')
    p.add_argument('--import-decisions', metavar='FILE',
                   help='record per-beat decisions downloaded from the page; `reshoot accept` is the one-step route')
    p.add_argument('--serve', action='store_true', help='serve the page on this computer and accept or reject the run '
                   'there, as `reshoot accept` does; stops once you decide')
    p.add_argument('--port', type=int, help='with --serve, the port (default: a free one)')
    p.add_argument('--no-open', action='store_true', help='with --serve, print the address without opening a browser')
    p.set_defaults(run=lambda a: review.serve(a) if a.serve else review.main(a))

    from reshoot import styles
    p = sub.add_parser('style', help='choose, save or reuse a visual style',
                       description='Apply caption placement and colours, title-card colours and browser framing '
                       'without changing the story, timing, fonts, audio or exports. Styles become ordinary '
                       'storyboard and edit settings. Update the preview afterwards.\n\n'
                       '    reshoot style list --project demo\n'
                       '    reshoot style apply midnight --project demo\n'
                       '    reshoot style save "Launch look" --project demo --out launch-style.toml', formatter_class=Examples)
    operations = p.add_subparsers(dest='operation', required=True)
    for operation, help_text in [('list', 'list starting looks and saved project styles'),
                                 ('apply', 'apply a listed style or portable style TOML file'),
                                 ('save', 'save the current look for reuse')]:
        command = operations.add_parser(operation, help=help_text)
        command.add_argument('--project', default='demo', help='project folder or reshoot.toml (default: demo)')
        if operation == 'apply':
            command.add_argument('style', help='a listed style name or path to a style TOML file')
        elif operation == 'save':
            command.add_argument('name', help='a name for the current look')
            command.add_argument('--out', help='export a portable style file instead of saving in the project library')
            command.add_argument('--replace', action='store_true', help='replace an existing saved style or export file')
        command.set_defaults(run=styles.main)

    from reshoot import framing
    p = sub.add_parser('frame', help='set destination framing or inspect measured readability',
                       description='Set Fit or Crop, a crop position and a viewing width for an export. '
                       'Update preview to render the choice and measure text sizes and clipping. Feedback is '
                       'an editing hint, not an automatic readability verdict.\n\n'
                       '    reshoot frame set 1 --fit crop --x 50 --y 50 --view-width 390 --project demo\n'
                       '    reshoot frame check demo/latest', formatter_class=Examples)
    operations = p.add_subparsers(dest='operation', required=True)
    command = operations.add_parser('set', help='change an export, numbered from 1')
    command.add_argument('export', type=int)
    command.add_argument('--project', default='demo')
    command.add_argument('--fit', choices=['contain', 'crop'])
    command.add_argument('--x', type=float, help='horizontal crop position: 0 left, 50 centre, 100 right')
    command.add_argument('--y', type=float, help='vertical crop position: 0 top, 50 centre, 100 bottom')
    command.add_argument('--view-width', dest='display_width', type=int, help='intended viewing width in pixels, 160 to 1920')
    command.set_defaults(run=framing.main)
    command = operations.add_parser('record', help='set the first browser take\'s view and record again on Update preview')
    command.add_argument('--project', default='demo')
    command.add_argument('--size', required=True, help='CSS width x height @ pixel ratio, such as 640x480@2')
    command.set_defaults(run=framing.main)
    command = operations.add_parser('check', help='read the measurements bound to a rendered run')
    command.add_argument('run_path')
    command.set_defaults(run=framing.main)

    from reshoot import tours
    p = sub.add_parser('tour', help='build an offline clickable walkthrough from checked beats',
                       description='A tour is one HTML file with its checked result images embedded. It works offline '
                       'and moves between captured screens. Create from checked beats, edit step words and optional '
                       'click markers, then Update preview or re-cut.\n\n'
                       '    reshoot tour create --title "Save and find a note" --project demo\n'
                       '    reshoot tour set 1 --text "The saved note appears in the list." --x 50 --y 40 --project demo\n'
                       '    reshoot recut demo/latest', formatter_class=Examples)
    operations = p.add_subparsers(dest='operation', required=True)
    for operation in ('create', 'title', 'set', 'add', 'move', 'remove', 'disable'):
        command = operations.add_parser(operation)
        command.add_argument('--project', default='demo')
        if operation in ('create', 'title'):
            command.add_argument('--name', help='safe output name; default demo-tour on creation')
            command.add_argument('--title')
        if operation in ('set', 'move', 'remove'):
            command.add_argument('step', type=int, help='step number starting at 1')
        if operation == 'move':
            command.add_argument('--to', type=int, required=True)
        if operation in ('set', 'add'):
            command.add_argument('--take', type=int, help='take number starting at 1')
            command.add_argument('--beat', required=operation == 'add')
            command.add_argument('--title')
            command.add_argument('--text')
            command.add_argument('--alt')
            command.add_argument('--width', type=int)
            command.add_argument('--crop', type=float, nargs=4, metavar=('LEFT', 'TOP', 'WIDTH', 'HEIGHT'))
            command.add_argument('--x', type=float, help='marker horizontal position, 0 to 100 percent')
            command.add_argument('--y', type=float, help='marker vertical position, 0 to 100 percent')
            command.add_argument('--no-marker', action='store_true')
        command.set_defaults(run=tours.main)

    from reshoot import screenshots
    p = sub.add_parser('screenshot', help='keep documentation PNGs current with checked beats',
                       description='Select result frames from TOML browser takes for documentation. Each selected '
                       'beat must have passing result checks. Update preview renders stable PNGs and includes '
                       'them in scanning and review; export copies them locally with the videos.\n\n'
                       '    reshoot screenshot set search-result --beat search --alt "Search shows the saved note" --project demo\n'
                       '    reshoot screenshot list --project demo', formatter_class=Examples)
    operations = p.add_subparsers(dest='operation', required=True)
    for operation in ('set', 'remove', 'list'):
        command = operations.add_parser(operation, help={'set': 'add or update a named screenshot',
            'remove': 'stop exporting a named screenshot', 'list': 'list configured documentation screenshots'}[operation])
        command.add_argument('--project', default='demo')
        if operation != 'list':
            command.add_argument('name')
        if operation == 'set':
            command.add_argument('--beat')
            command.add_argument('--alt', help='one-line description, up to 300 characters')
            command.add_argument('--take', type=int, help='browser take number, starting at 1 (default first)')
            width = command.add_mutually_exclusive_group()
            width.add_argument('--width', type=int, help='maximum image width; never enlarges the source')
            width.add_argument('--native', action='store_true', help='keep the captured pixel dimensions')
            crop = command.add_mutually_exclusive_group()
            crop.add_argument('--crop', type=float, nargs=4, metavar=('LEFT', 'TOP', 'WIDTH', 'HEIGHT'),
                              help='crop fractions from 0 to 1 within the captured viewport')
            crop.add_argument('--full-frame', action='store_true', help='remove cropping and use the captured viewport')
        command.set_defaults(run=screenshots.main)

    from reshoot import audio
    p = sub.add_parser('audio', help='audition narration and balance voice and music',
                       description='Save narration for a beat, audition its saved voice before recording, or change '
                       'the final mix. Narration changes record a fresh preview; mix changes reuse the recording. '
                       'Volume values are linear gains, with 1 as the original level.\n\n'
                       '    reshoot audio set --beat search --text "Find the matching note." --project demo\n'
                       '    reshoot audio audition search --project demo\n'
                       '    reshoot audio set --music-volume 0.15 --voice-volume 1 --duck --project demo',
                       formatter_class=Examples)
    operations = p.add_subparsers(dest='operation', required=True)
    command = operations.add_parser('set', help='save a narration line, voice or mix settings')
    command.add_argument('--project', default='demo')
    command.add_argument('--beat', help='beat ID for --text')
    command.add_argument('--text', help='spoken words; empty text removes the line')
    command.add_argument('--engine', help='speech command, such as say -v Samantha; empty uses the system default')
    command.add_argument('--voice-volume', type=float, help='voice gain from 0 to 2 (default 1)')
    command.add_argument('--music-volume', type=float, help='music gain from 0 to 1 (default 0.25)')
    command.add_argument('--duck', action=argparse.BooleanOptionalAction, default=None,
                         help='lower music while narration speaks (default on)')
    command.set_defaults(run=audio.main)
    command = operations.add_parser('audition', help='speak and cache one saved line without recording the app')
    command.add_argument('beat')
    command.add_argument('--project', default='demo')
    command.add_argument('--expected-key', help=argparse.SUPPRESS)
    command.set_defaults(run=audio.main)

    from reshoot import sequence
    p = sub.add_parser('sequence', help='trim and arrange the video by recorded beats',
                       description='Choose inclusive beat ranges, move, duplicate, add or remove video parts. '
                       'The storyboard still runs in full, with its actions and checks unchanged. Numbers for '
                       'parts, positions and takes start at 1. Update preview after editing.\n\n'
                       '    reshoot sequence list --project demo\n'
                       '    reshoot sequence range 1 --from add --through search --project demo\n'
                       '    reshoot sequence duplicate 1 --project demo\n'
                       '    reshoot sequence move 2 --to 1 --project demo', formatter_class=Examples)
    operations = p.add_subparsers(dest='operation', required=True)
    for operation, label in [('list', 'show the cut and recorded beat names'), ('range', 'choose a part\'s inclusive beat range'),
                             ('move', 'move a part to a position'), ('duplicate', 'repeat a part'),
                             ('remove', 'remove a video part'), ('add', 'append a recorded beat range')]:
        command = operations.add_parser(operation, help=label)
        command.add_argument('--project', default='demo', help='project folder or reshoot.toml (default: demo)')
        command.add_argument('--run', dest='run_path', help='use this complete run from the project (default: latest)')
        if operation not in ('list', 'add'):
            command.add_argument('part', type=int, help='part number, starting at 1')
        if operation in ('range', 'add'):
            command.add_argument('--from', dest='start', required=True, help='first beat to include')
            command.add_argument('--through', required=True, help='last beat to include, with its result hold')
        if operation == 'move':
            command.add_argument('--to', type=int, required=True, help='new position, starting at 1')
        if operation == 'add':
            command.add_argument('--take', type=int, default=1, help='recorded take number (default: 1)')
        command.set_defaults(run=sequence.main)

    from reshoot import studio
    p = sub.add_parser('studio', help='shape a demo in a browser: captions, holds, undo, preview, final and review',
                       description='Open a page on this computer for shaping a demo: the latest run\'s video with its '
                       'beats on a timeline, each beat\'s frame, result checks and caption, and what the scan found. '
                       'Captions and holds save as you leave a field. Undo and Redo restore studio edits; source '
                       'changes in another editor require a reload. Update preview chooses a re-cut for caption '
                       'or edit changes and a recording for timing, actions or settings. Make final records the '
                       'full-size run. Inspect scan sheets and accept the exact run shown. Updates can be cancelled. '
                       'Style and exports offers starting looks, saved styles, portable import/export, cards, '
                       'frame, music and export presets. Applying a style is one undoable change. '
                       'Your cut chooses beat ranges and moves, repeats or removes video parts without changing the task. '
                       'It serves on 127.0.0.1 behind a random address until Ctrl-C.\n\n'
                       '    reshoot studio\n'
                       '    reshoot studio app/demo --port 8800 --no-open', formatter_class=Examples)
    p.add_argument('project', nargs='?', default='demo', help='the project folder or its reshoot.toml (default: demo)')
    p.add_argument('--port', type=int, help='the port (default: a free one)')
    p.add_argument('--no-open', action='store_true', help='print the address without opening a browser')
    p.set_defaults(run=studio.serve)
    p = sub.add_parser('accept', help='accept a run after watching it: exports, beats and scan items in one step',
                       description='Accept a run after watching its exports and looking at its scan sheets. Unflagged '
                       'items are accepted together; each flagged item must be named with --flagged or --reject. The '
                       'verdict is bound to the run\'s exact files and scan policy.')
    p.add_argument('run_path', help='the run folder, such as demo/takes/runs/ID or demo/latest')
    p.add_argument('--flagged', nargs='+', metavar='LABEL', help='flagged items you inspected and accept')
    p.add_argument('--reject', nargs='+', metavar='LABEL', help='items that must not be shared; marks the run failed')
    p.add_argument('--yes', action='store_true', help='skip the confirmation; only for the owner\'s own scripts')
    p.add_argument('--preview', action='store_true', help='accept a preview, which is otherwise refused')
    p.set_defaults(run=review.accept)
    p = sub.add_parser('export', help='copy a run\'s videos and GIFs to a local directory', description=runs)
    p.add_argument('run_path', help='the run to copy from, such as demo/latest')
    p.add_argument('--directory', help='where to copy the media, such as docs/demo')
    p.add_argument('--file', action='append', help='copy only this file listed in run.json, such as '
                   'takes/demo-final.mp4; without it, the run\'s videos, GIFs, subtitles, documentation PNGs and offline tour HTML')
    p.add_argument('--replace', action='store_true', help='overwrite media already in --directory, such as the repo\'s demo')
    p.add_argument('--record', metavar='DIR', help='also write the run\'s small record (report, beat results, evidence '
                   'frames) to DIR, such as demo/accepted, for later comparisons')
    p.add_argument('--markdown', metavar='FILE', help='write Markdown showing the copied GIF and video and each scan '
                   'finding, with its frame when --record is given, such as for a pull request')
    p.add_argument('--link', metavar='URL', help='with --markdown, the URL that repository paths are added to, such as '
                   'https://github.com/OWNER/REPO/blob/BRANCH/')
    p.set_defaults(run=project.export)
    a = ap.parse_args(argv)
    try:
        sys.exit(a.run(a) or 0)
    except (ValueError, OSError) as e:
        from reshoot.safety import redact
        ap.exit(2, redact(str(e)) + '\n')


def run_script(a):
    from pathlib import Path
    if Path(a.script).suffix == '.toml':
        from reshoot.timeline import edit
        return edit(a)
    import runpy
    sys.argv = [a.script, *a.args]
    runpy.run_path(a.script, run_name="__main__")


if __name__ == "__main__":
    main()
