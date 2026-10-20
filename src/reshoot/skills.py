"""Install complete primary skills from the same source used by the plugin."""
import shutil
from importlib.resources import files
from pathlib import Path

NAMES = ('reshoot-demo', 'reshoot-refresh', 'reshoot-review')


def install(a):
    base = Path(a.directory).resolve()
    target = base / ('.agents' if a.harness == 'codex' else '.claude') / 'skills'
    source = files('reshoot').joinpath('bundled_skills')
    # Editable installs use the canonical repository source.
    if not source.is_dir():
        source = Path(__file__).resolve().parents[2] / 'skills'
    if not source.is_dir():
        raise ValueError('skill bundle missing from this installation')
    for name in NAMES:
        if (target / name).exists():
            raise ValueError(f'will not overwrite existing skill: {name}')
        if not source.joinpath(name, 'SKILL.md').is_file():
            raise ValueError(f'incomplete skill bundle: {name}')
    target.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        shutil.copytree(str(source.joinpath(name)), target / name)
        print(target / name)
