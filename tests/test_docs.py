"""The docs stay short and in plain words: see docs/plans/2026-10-25-docs-simplification.md."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / 'README.md', *sorted((ROOT / 'guide').glob('*.md')), *sorted((ROOT / 'skills').glob('**/*.md'))]
# Words for how the code keeps things safe, not for what the reader does
INTERNAL = ['binding', 'bound to', 'revision guard', 'stale-evidence', 'stale evidence', 'checkpointed',
            'interprocess', 'materializ', 'hashed measurements', 'pending-range', 'provenance']


def words(path):
    """Words of prose: code blocks, link targets and table rules left out."""
    text = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
    return len(re.findall(r"[A-Za-z][\w'.-]*", re.sub(r'\]\([^)]*\)', ']', text)))


def test_docs_use_no_em_dashes_or_internal_words():
    for page in PAGES:
        text = page.read_text()
        assert '—' not in text, f'{page.relative_to(ROOT)} has an em dash'
        found = [w for w in INTERNAL if w in text.lower()]
        assert not found, f'{page.relative_to(ROOT)} uses {found}; say what the reader does instead'


def test_the_readme_and_skills_stay_short():
    assert words(ROOT / 'README.md') < 1000
    for skill in (ROOT / 'skills').glob('*/SKILL.md'):
        assert words(skill) < 1200, f'{skill.relative_to(ROOT)} is {words(skill)} words; move reference text to the guide'
