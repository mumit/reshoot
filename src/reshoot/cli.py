"""reshoot: demo videos of software, made from scripts so you can shoot them again when the app changes."""
import argparse, sys


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reshoot", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    from reshoot import web, window, check
    p = sub.add_parser("web", help="record a web page acting out a storyboard, in headless Chrome",
                       description=web.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("storyboard"); p.add_argument("out", help="the video to write, such as takes/web.mp4")
    p.add_argument("--url", help="the page to open (default: the storyboard's URL)")
    p.add_argument("--size", help="CSS width x height @ device pixel ratio, such as 390x844@3 (default 1280x720@1.5)")
    p.add_argument("--theme", choices=["dark", "light"])
    p.add_argument("--mobile", action="store_true", help="a phone: touch and a mobile viewport")
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
    p.add_argument("--fail", nargs="+", metavar="LABEL", help="these failed")
    p.add_argument("--ok", action="store_true", help="every other image on the sheets passed")
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

    from reshoot import run
    p = sub.add_parser("run", help="run a whole shoot from a reshoot.toml: the app, every take, the cut and the check",
                       description=run.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("config", nargs="?", default="reshoot.toml")
    p.set_defaults(run=run.main)

    p = sub.add_parser("edit", help="run an edit script that uses reshoot.cut, passing it the rest of the arguments")
    p.add_argument("script"); p.add_argument("args", nargs=argparse.REMAINDER)
    p.set_defaults(run=run_script)

    a = ap.parse_args(argv)
    sys.exit(a.run(a) or 0)


def run_script(a):
    import runpy
    sys.argv = [a.script, *a.args]
    runpy.run_path(a.script, run_name="__main__")


if __name__ == "__main__":
    main()
