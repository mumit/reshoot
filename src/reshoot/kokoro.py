"""Optional, local English narration. Model and voice downloads happen on first use."""
import functools
import math
import re
import shlex

VOICES = {'af_heart': 'Heart · American English', 'af_bella': 'Bella · American English',
          'am_michael': 'Michael · American English', 'bf_emma': 'Emma · British English'}


def settings(engine):
    """Validate before loading dependencies or downloading any model files."""
    parts = shlex.split(engine)
    name, speed = 'af_heart', 1.0
    seen = set()
    for index in range(1, len(parts), 2):
        option = parts[index]
        if option not in ('--voice', '--speed') or option in seen or index + 1 == len(parts):
            raise ValueError('Use kokoro [--voice af_heart] [--speed 1]; speed is 0.5 to 2.')
        seen.add(option)
        if option == '--voice':
            name = parts[index + 1]
        else:
            try:
                speed = float(parts[index + 1])
            except ValueError:
                raise ValueError('Kokoro speed must be a number from 0.5 to 2.') from None
    if not re.fullmatch(r'[ab][fm]_[a-z]+', name):
        raise ValueError('Choose an English Kokoro voice ID, such as af_heart or bf_emma.')
    if not math.isfinite(speed) or not .5 <= speed <= 2:
        raise ValueError('Kokoro speed must be a number from 0.5 to 2.')
    return name, speed


@functools.lru_cache(maxsize=2)
def pipeline(language):
    try:
        from kokoro import KPipeline
    except ImportError:
        raise ValueError('Install local neural narration with uv tool install --upgrade "reshoot[kokoro]" '
                         '(from source: uv sync --extra browser --extra kokoro).') from None
    # CPU works on both macOS and Linux without a GPU-specific installation.
    return KPipeline(lang_code=language, repo_id='hexgrad/Kokoro-82M', device='cpu')


def render(text, out, engine):
    """Write 24 kHz audio and return model-timed word spans, with chunk offsets."""
    name, speed = settings(engine)
    model = pipeline(name[0])
    import soundfile as sf
    words, samples = [], 0
    with sf.SoundFile(str(out), mode='w', samplerate=24000, channels=1, subtype='PCM_16') as file:
        # Pass connected text; let Kokoro split only at its own context limit.
        for result in model(text, voice=name, speed=speed):
            if result.audio is None:
                raise ValueError('Kokoro produced no audio for this passage.')
            data = result.audio.detach().cpu().numpy()
            offset = samples / 24000
            for token in result.tokens or []:
                if token.start_ts is not None and token.end_ts is not None:
                    words.append({'text': token.text + token.whitespace,
                                  'start': offset + token.start_ts, 'end': offset + token.end_ts})
            file.write(data)
            samples += len(data)
    if not samples:
        raise ValueError('Save some spoken words before auditioning Kokoro.')
    return words
