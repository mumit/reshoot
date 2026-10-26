"""Distribution checks for the source shared by the wheel and harness bundles."""
import json
import tomllib
from pathlib import Path
from reshoot.skills import NAMES


def test_primary_skills_have_frontmatter_and_codex_metadata():
    root = Path(__file__).resolve().parents[1]
    for name in NAMES:
        folder = root / 'skills' / name
        text = (folder / 'SKILL.md').read_text()
        header = text.split('---', 2)[1]
        assert 'name: ' + name in header and 'description: ' in header
        assert 'Requires reshoot CLI 0.3.9' in text
        assert '../../' not in text
        metadata = (folder / 'agents/openai.yaml').read_text()
        assert '$' + name in metadata and 'short_description:' in metadata
    plugin = json.loads((root / '.claude-plugin/plugin.json').read_text())
    package = tomllib.loads((root / 'pyproject.toml').read_text())['project']
    assert plugin['version'] == package['version']
