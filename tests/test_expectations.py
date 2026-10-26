"""A correction changes an intended result, never its control or the task."""
import tomllib

import pytest
from reshoot import expectations, studio
from reshoot.workspace import History


@pytest.mark.parametrize('kind,key,before,after', [
    ('count', 'count', 0, 1), ('text', 'contains', 'old words', 'new words'),
    ('url', 'contains', '/old', '/new'), ('value', 'value', 'old', ''),
    ('checked', 'checked', True, False),
])
def test_correction_preserves_target_actions_comments_and_other_checks(tmp_path, kind, key, before, after):
    from reshoot.workspace import quote
    board = tmp_path / 'storyboard.toml'
    board.write_text('schema_version=1\nurl="http://localhost/"\n[[beat]]\nid="result"\n'
                     '[[beat.action]]\ntype="click"\ntarget={css="#save"}\n'
                     f'[[beat.expect]] # keep this check\ntype="{kind}"\ntarget={{css="#result"}}\n'
                     f'{key}={quote(before)} # why this result matters\n'
                     'timeout=1500\n[[beat.expect]]\ntype="visible"\ntarget={css="#saved"}\n')
    original = board.read_bytes()
    old = tomllib.loads(board.read_text())['beat'][0]
    history = History([board])
    history.change(lambda: studio.edit(board, {'beat': 'result', 'update_expect': 0, 'expect': old['expect'][0], 'value': after}))
    new = tomllib.loads(board.read_text())['beat'][0]
    assert new['expect'] == [{**old['expect'][0], key: after}, old['expect'][1]]
    assert new['action'] == old['action']
    assert '# why this result matters' in board.read_text() and '# keep this check' in board.read_text()
    history.move('undo')
    assert board.read_bytes() == original
    history.move('redo')
    assert tomllib.loads(board.read_text())['beat'][0] == new
    with pytest.raises(ValueError, match='changed since the page loaded'):
        studio.edit(board, {'beat': 'result', 'update_expect': 0, 'expect': old['expect'][0], 'value': after})


@pytest.mark.parametrize('kind,value', [('count', True), ('count', -1), ('count', 1.5),
                                      ('text', ''), ('text', None), ('checked', 'false'), ('value', 2)])
def test_invalid_correction_never_changes_the_lines(kind, value):
    from reshoot.workspace import quote
    key = expectations.VALUES[kind]
    old = 1 if kind == 'count' else True if kind == 'checked' else 'expected'
    expected = {'type': kind, 'target': {'css': '#result'}, key: old}
    lines = ['[[beat]]\n', 'id="result"\n', '[[beat.expect]]\n', f'type="{kind}"\n',
             'target={css="#result"}\n', f'{key}={quote(old)}\n']
    original = list(lines)
    with pytest.raises(ValueError):
        expectations.update_check(lines, 'result', 0, expected, value)
    assert lines == original
