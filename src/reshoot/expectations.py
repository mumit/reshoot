"""Explain and correct a result check while preserving its target and neighboring story."""
import html
import json
import re
import tomllib

from reshoot.workspace import put, tables

VALUES = {'count': 'count', 'text': 'contains', 'url': 'contains', 'value': 'value', 'checked': 'checked'}


def span(lines, beat, index, expected):
    heads = tables(lines, '[[beat]]')
    found = next((n for n, (_, start, end) in enumerate(heads)
                  if tomllib.loads(''.join(lines[start:end])).get('id') == beat), None)
    if found is None:
        raise ValueError(f'no beat {beat!r} in the storyboard')
    end = heads[found + 1][0] if found + 1 < len(heads) else len(lines)
    checks = [(head, stop) for head, _, stop in tables(lines, '[[beat.expect]]') if heads[found][0] < head < end]
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(checks):
        raise ValueError('That result check is no longer in the storyboard. Reload the project.')
    head, stop = checks[index]
    if tomllib.loads(''.join(lines[head + 1:stop])) != expected:
        raise ValueError('That result check changed since the page loaded. Reload the project.')
    return head, stop


def without_check(lines, beat, index, expected):
    head, stop = span(lines, beat, index, expected)
    while stop > head + 1 and not lines[stop - 1].strip():
        stop -= 1
    return lines[:head] + lines[stop:]


def update_check(lines, beat, index, expected, value):
    head, stop = span(lines, beat, index, expected)
    key = VALUES.get(expected.get('type'))
    if key is None:
        raise ValueError('This check has no expected value to change. Change its target in the storyboard.')
    if key == 'count':
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError('The expected count must be a nonnegative integer.')
    elif key == 'checked':
        if not isinstance(value, bool):
            raise ValueError('The expected state must be ticked or not ticked.')
    elif not isinstance(value, str) or len(value) > 4000 or (key == 'contains' and not value.strip()):
        raise ValueError('Enter the expected words, up to 4000 characters.')
    put(lines, (head + 1, stop), key, value)
    return lines


def form(check, disabled=False):
    """Offer a correction without guessing that the current app result is the intended one."""
    e = lambda value: html.escape(str(value), quote=True)
    entry = check['expect']
    key = VALUES.get(entry.get('type'))
    if key is None:
        return ''
    value = entry.get(key, True if key == 'checked' else '')
    if key == 'count':
        field = f'<label>Expected number of matches <input name="value" type="number" min="0" step="1" value="{e(value)}" required></label>'
    elif key == 'checked':
        field = ('<label>Expected state <select name="value">'
                 f'<option value="true"{" selected" if value else ""}>Ticked</option>'
                 f'<option value="false"{"" if value else " selected"}>Not ticked</option></select></label>')
    else:
        label = 'Expected address contains' if entry['type'] == 'url' else 'Expected field value' if key == 'value' else 'Expected text contains'
        field = f'<label>{label} <textarea name="value" maxlength="4000" rows="2"{" required" if key == "contains" else ""}>{e(value)}</textarea></label>'
    return (f'<form class="check-correction" data-beat="{e(check["beat"])}" data-index="{check["index"]}" '
            f'data-expect="{e(json.dumps(entry))}" data-kind="{entry["type"]}">'
            f'<fieldset{" disabled" if disabled else ""}>'
            '<p>Keep this check if it proves the task worked. Change its expected result only when the story should show something different.</p>'
            f'{field}<p class="hint">The control and the other result checks stay the same. A new preview must verify this result.</p>'
            '<button type="submit">Save expected result</button> <button type="reset">Reset</button></fieldset></form>')


def explain(n, beat, entry, error):
    """Describe an expected result and the recorded mismatch in plain words."""
    target = entry.get('target') or {}
    where = (f'`{target["css"]}`' if 'css' in target else f'test id "{target["test_id"]}"' if 'test_id' in target
             else f'the {target.get("role")} "{target.get("name", "")}"' if 'role' in target else 'the page')
    actual = re.search(r'Actual value: (.+)', error or '')
    actual = actual[1].strip().strip('"') if actual else None
    step = f'Step {n} ({beat})'
    kind = entry.get('type')
    if kind == 'count':
        want = entry.get('count')
        what = 'no elements' if want == 0 else f'{want} element{"" if want == 1 else "s"}'
        return f'{step} expected {what} matching {where}' + (f', but the page had {actual}.' if actual else ', but the count was different.')
    if kind == 'text':
        shown = f', but it showed "{actual[:80]}"' if actual else ", but it didn't"
        return f'{step} expected {where} to contain "{entry.get("contains")}"{shown}.'
    if kind == 'visible':
        return f"{step} expected {where} to be visible, but it wasn't."
    if kind == 'url':
        return f'{step} expected the address to contain "{entry.get("contains")}"' + (f', but it was {actual}.' if actual else ", but it didn't.")
    if kind == 'value':
        return f'{step} expected {where} to hold "{entry.get("value")}"' + (f', but it held "{actual}".' if actual else '.')
    if kind == 'checked':
        return f'{step} expected {where} to be {"ticked" if entry.get("checked", True) else "not ticked"}.'
    return f"{step}'s result check didn't pass."
