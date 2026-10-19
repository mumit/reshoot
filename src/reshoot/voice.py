"""A voiceover from text: each line is spoken once, before recording, so reshoot knows how long it takes and each
beat can wait for its line to finish.

    VOICE = {"home": "Notes keeps your lists in one place.", "search": "Find any note as you type."}
    VOICE_ENGINE = "say -v Samantha"            # optional: see below

The keys are beat names; a line starts with its beat. By default the voice is macOS's `say`, or `espeak-ng` (or
`espeak`) elsewhere. VOICE_ENGINE can be any command that reads the text on stdin and writes a sound file to
{out}, such as a script that calls a text-to-speech service:

    VOICE_ENGINE = "python3 tools/demo/tts.py {out}"

reshoot never handles a service's key: the command does, from its own environment.
"""
import json, platform, shlex, shutil, subprocess
from pathlib import Path


def engine_command(engine=None):
    """The command for an engine setting, with {out} for the file to write; text goes on stdin."""
    if engine and "{out}" in engine:
        return engine
    if engine and engine.split()[0] == "say":
        return f"{engine} -o {{out}} -f -"
    if engine and engine.split()[0] in ("espeak-ng", "espeak"):
        return f"{engine} -w {{out}} --stdin"
    if engine:
        raise SystemExit(f"VOICE_ENGINE {engine!r} needs {{out}} where the sound file goes (text comes on stdin)")
    if platform.system() == "Darwin" and shutil.which("say"):
        return "say -o {out} -f -"
    for e in ("espeak-ng", "espeak"):
        if shutil.which(e):
            return f"{e} -w {{out}} --stdin"
    raise SystemExit("no text-to-speech here: install espeak-ng, or set VOICE_ENGINE to a command")


def speak(text, out, engine=None):
    """Writes text, spoken, to out (a .wav at 48 kHz, mono); returns its length in seconds."""
    from reshoot.cut import duration, ff
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = out.with_suffix(".raw" + (".aiff" if engine_command(engine).startswith("say") else ".wav"))
    cmd = engine_command(engine).replace("{out}", shlex.quote(str(raw)))
    r = subprocess.run(cmd, shell=True, input=text.encode(), capture_output=True)
    if r.returncode or not raw.exists():
        raise SystemExit(f"the voice command failed ({cmd}): {r.stderr.decode(errors='replace').strip()[:300]}")
    ff("-i", raw, "-ar", 48000, "-ac", 1, out)
    raw.unlink()
    return duration(out)


def prepare(lines, folder, engine=None):
    """Speaks each beat's line into folder; returns {beat: (file, seconds)}. A line already spoken with the same
    words and engine isn't spoken again."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    done = json.loads((folder / "lines.json").read_text()) if (folder / "lines.json").exists() else {}
    out = {}
    for i, (beat, text) in enumerate(lines.items()):
        f = folder / f"{i:02}-{beat}.wav"
        key = f"{engine}|{text}"
        if done.get(beat, {}).get("key") == key and f.exists():
            out[beat] = (str(f), done[beat]["seconds"])
            continue
        print(f"  speaking {beat!r}", flush=True)
        out[beat] = (str(f), speak(text, f, engine))
        done[beat] = {"key": key, "seconds": out[beat][1], "text": text}
    (folder / "lines.json").write_text(json.dumps(done, indent=1))
    return out
