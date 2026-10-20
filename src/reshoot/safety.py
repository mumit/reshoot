"""Safe descriptions for logs and reports. Never print raw source URLs."""
import hashlib
import re
from urllib.parse import urlsplit


def describe(source):
    value = str(source)
    if value.startswith(('http://', 'https://')):
        return 'remote source ' + hashlib.sha256(value.encode()).hexdigest()[:12]
    return redact(value)


def redact(value):
    value = str(value)
    value = re.sub(r'https?://[^\s\"\'<>]+', lambda m: describe(m[0]), value)
    value = re.sub(r'\b(?:sk-[\w-]{8,}|gh[pousr]_[\w]+|github_pat_[\w]+|xox[abpr]-[\w-]+|AKIA[0-9A-Z]{16})', '[secret]', value)
    value = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[email]', value)
    value = re.sub(r'(/Users/|/home/)[^/\s]+', r'\1[user]', value)
    value = re.sub(r'(?i)(token|password|secret|api[_-]?key)(\s*[=:]\s*)[^\s,;]+', r'\1\2[secret]', value)
    return value
