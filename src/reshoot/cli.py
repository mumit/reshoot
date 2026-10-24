"""reshoot: demo videos of software, made from scripts so you can shoot them again when the app changes."""
import argparse, sys


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reshoot", description=__doc__)
    from importlib.metadata import version
    ap.add_argument("--version", action="version", version=version("reshoot"))
    sub = ap.add_subparsers(dest="cmd", required=True)

    from reshoot import web, window, check, story
    p = sub.add_parser("web", help="record a web page acting out a storyboard, in headless Chrome",
                       description=story.__doc__ + "\nLegacy Python storyboards\n\n" + web.__doc__,
                       formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("storyboard"); p.add_argument("out", help="the video to write, such as takes/web.mp4")
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
    p.add_argument("-s", "--seconds", type=int, default=8)
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
    p.add_argument("--text-file", action="append", default=[], help="scan exact subtitle (.srt) or narration (.voice.json) text")
    p.add_argument("--ocr", choices=["auto", "vision", "tesseract"], help="explicit OCR backend; failures never silently fall back")
    p.add_argument("--no-scan", dest="scan", action="store_false", help="don't scan for likely problems")
    p.set_defaults(run=check.main)

    from reshoot import cut
    p = sub.add_parser("gif", help="a GIF of part of a take, between two beats or times")
    p.add_argument("take"); p.add_argument("out")
    p.add_argument("start", help="a beat name from TAKE.beats.json, or seconds")
    p.add_argument("end", nargs="?", help="a beat name or seconds (default: the end of the take)")
    p.add_argument("--fps", type=int, default=15); p.add_argument("--width", type=int, default=800)
    p.set_defaults(run=cut.gifs_main)

    p = sub.add_parser("last-change", help="when a take last changed, such as when a command in a terminal finished")
    p.add_argument("take")
    p.set_defaults(run=lambda a: print(f"{cut.last_change(a.take):.2f}"))

    from reshoot import rec
    p = sub.add_parser("rec", help="write a storyboard by clicking and typing through the app in Chrome",
                       description=rec.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url"); p.add_argument("out", help="the storyboard to write, such as tools/demo/storyboard.py")
    p.add_argument("--size", default="1280x720@1.5", help="the page size the storyboard is for (default 1280x720@1.5)")
    p.add_argument("--headless", action="store_true", help=argparse.SUPPRESS)
    p.set_defaults(run=rec.main)

    from reshoot import run
    p = sub.add_parser("run", help="run a whole shoot from a reshoot.toml: the app, every take, the cut and the check",
                       description=run.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("config", nargs="?", default="reshoot.toml")
    p.set_defaults(run=run.main)

    p = sub.add_parser("edit", help="run an edit script that uses reshoot.cut, passing it the rest of the arguments")
    p.add_argument("script"); p.add_argument("args", nargs=argparse.REMAINDER)
    p.set_defaults(run=run_script)

    from reshoot import project
    p = sub.add_parser('doctor', help='check project tools without recording')
    p.add_argument('--config')
    p.add_argument('--json', action='store_true')
    p.set_defaults(run=project.doctor)
    p = sub.add_parser('init', help='create a demo project from packaged templates')
    p.add_argument('directory', nargs='?', default='.')
    p.add_argument('--url', help='your demo app; omit to use the made-up notes example')
    p.set_defaults(run=project.init)
    p = sub.add_parser('preview', help='record an isolated lower-resolution preview')
    p.add_argument('config', nargs='?', default='reshoot.toml')
    p.add_argument('--from', dest='from_beat', help='partial preview, replaying setup and earlier actions')
    p.set_defaults(run=run.preview)
    from reshoot import skills
    p = sub.add_parser('skills', help='install the primary reshoot skills for a harness')
    p.add_argument('harness', choices=['codex', 'claude'])
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
    p.set_defaults(run=review.main)
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
    p = sub.add_parser('export', help='copy explicitly chosen run media to a local directory', description=runs)
    p.add_argument('run_path', help='the run to copy from, such as demo/latest')
    p.add_argument('--directory', help='where to copy the chosen --file media')
    p.add_argument('--file', action='append', help='a file listed in run.json, such as takes/demo-final.mp4')
    p.add_argument('--replace', action='store_true', help='overwrite media already in --directory, such as the repo\'s demo')
    p.add_argument('--record', metavar='DIR', help='also write the run\'s small record (report, beat results, evidence '
                   'frames) to DIR, such as demo/accepted, for later comparisons')
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
