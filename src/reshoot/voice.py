"""A voiceover from text: each line is spoken once, before recording, so reshoot knows how long it takes and each
beat can wait for its line to finish.

    VOICE = {"home": "Notes keeps your lists in one place.", "search": "Find any note as you type."}
    VOICE_ENGINE = "say -v Samantha"            # optional: see below

The keys are beat names; a line starts with its beat. By default the voice is macOS's `say`, or `espeak-ng` (or
`espeak`) elsewhere. Set VOICE_ENGINE = "kokoro --voice af_heart" for optional local neural English speech.
Other engines can be any command that reads the text on stdin and writes a sound file to
{out}, such as a script that calls a text-to-speech service:

    VOICE_ENGINE = "python3 tools/demo/tts.py {out}"

reshoot never handles a service's key: the command does, from its own environment.
"""
import json, platform, shlex, shutil, subprocess, hashlib, tempfile
from pathlib import Path


def engine_command(engine=None):
    """Normalize a built-in engine or a command with {out}; custom commands read stdin."""
    if engine and engine.split()[0] == 'kokoro':
        from reshoot.kokoro import settings
        name, speed = settings(engine)
        return f'kokoro --voice {name} --speed {speed:g}'
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


def speak(text, out, engine=None, cwd=None):
    """Writes text, spoken, to out (a .wav at 48 kHz, mono); returns its length in seconds."""
    from reshoot.cut import duration, ff
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='reshoot-voice-', dir=out.parent) as temp:
        command = engine_command(engine)
        raw = Path(temp) / ('raw.aiff' if command.startswith('say') else 'raw.wav')
        words = None
        if command.startswith('kokoro '):
            from reshoot.kokoro import render
            words = render(text, raw, command)
        else:
            cmd = command.replace('{out}', shlex.quote(str(raw)))
            r = subprocess.run(cmd, shell=True, input=text.encode(), capture_output=True, timeout=120, cwd=cwd)
            if r.returncode or not raw.exists():
                raise ValueError(f'voice command failed (exit {r.returncode})')
        finished = Path(temp) / 'line.wav'
        ff('-i', raw, '-ar', 48000, '-ac', 1, finished)
        finished.replace(out)
        if words is not None:
            out.with_suffix('.words.json').write_text(json.dumps(words) + '\n')
    return duration(out)


def cache_key(text, engine=None):
    return hashlib.sha256((engine_command(engine) + '\0' + text).encode()).hexdigest()


def prepare(lines, folder, engine=None, cwd=None):
    """Speaks each beat's line into folder; returns {beat: (file, seconds)}. A line already spoken with the same
    words and engine isn't spoken again."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    from reshoot.cut import duration
    out = {}
    for beat, text in lines.items():
        key = cache_key(text, engine)
        f = folder / (key + '.wav')
        if f.exists():
            out[beat] = (str(f), duration(f))
        else:
            print(f'  speaking {beat!r}', flush=True)
            out[beat] = (str(f), speak(text, f, engine, cwd=cwd))
    return out
