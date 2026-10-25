"""Looks for likely privacy problems in an image, so the check by eye starts with them: text that looks like an
email, a phone number, a key, a file path with a user name or a street address; words you list; and faces and
people.

Text is read with Apple's Vision on macOS, or Tesseract elsewhere (if installed). Faces and people need Vision. A
scan only points at problems; it never passes an image. Looking at every image is still the check.
"""
import io, platform, re, shutil, subprocess, os

PATTERNS = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")),
    ("key or token", re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|sk-ant-[\w-]{10,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}"
                                r"|xox[abpr]-[\w-]{10,}|AKIA[0-9A-Z]{16}|AIza[\w-]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY)")),
    ("long random string (a key?)", re.compile(r"\b(?=[A-Za-z0-9_-]*\d)(?=[A-Za-z0-9_-]*[A-Za-z])[A-Za-z0-9_-]{32,}\b")),
    ("file path with a user name", re.compile(r"(/Users/|/home/|[A-Z]:\\Users\\)[^/\\\s]+")),
    ("phone number", re.compile(r"(?<![\w.])\+?\(?\d[\d\s().-]{7,}\d(?![\w.])")),
    ("street address", re.compile(r"\b\d{1,5}\s+([A-Z][a-z]+\s){1,3}(Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|"
                                  r"Boulevard|Blvd|Court|Ct|Way|Crescent|Cres|Place|Pl)\b\.?")),
]
SAFE_EMAIL = re.compile(r"@example\.(com|org|net)$", re.I)


def reasons(text, watch=()):
    """What in a line of text looks private: [(reason, the matching part)]."""
    found = []
    for why, pat in PATTERNS:
        for m in pat.finditer(text):
            part = m.group(0)
            if why == "email" and SAFE_EMAIL.search(part):
                continue  # made-up addresses for demos
            if why == "phone number" and sum(c.isdigit() for c in part) < 9:
                continue
            if why == "long random string (a key?)" and any(r == "key or token" for r, _ in found):
                continue
            found.append((why, part))
    low = text.lower()
    for word in watch:
        if word and word.lower() in low:
            found.append((f'"{word}" (on your watch list)', word))
    return found


def backend(engine=None):
    engine = engine or os.environ.get('RESHOOT_OCR', 'auto')
    if engine not in ('auto', 'vision', 'tesseract'):
        raise ValueError('OCR backend must be auto, vision, or tesseract')
    if engine == 'auto':
        if platform.system() == 'Darwin':
            try:
                import Vision
                return 'vision'
            except ImportError:
                pass
        return 'tesseract'
    return engine


def can_scan(engine=None):
    """What this machine can look for: a set of "text", "people"."""
    if backend(engine) == "vision" and platform.system() == "Darwin":
        try:
            import Vision  # noqa: F401
            return {"text", "people"}
        except ImportError:
            pass
    return {"text"} if backend(engine) == "tesseract" and shutil.which("tesseract") else set()


def scan(im, watch=(), engine=None):
    """Flags for a PIL image: [(box (x, y, w, h) in its pixels, reason, what was found)]."""
    if backend(engine) == "vision":
        try:
            return _vision(im, watch)
        except ImportError:
            pass
    if backend(engine) == "tesseract" and shutil.which("tesseract"):
        return _tesseract(im, watch)
    raise RuntimeError("requested OCR backend unavailable")


_level = {}  # Vision's text reader on this Mac, found once


def vision_level():
    """'accurate', or 'fast' on a Mac whose accurate text reader fails (TextRecognition.CRImageReaderError 1 on some
    Macs). Tried once, on a small image of text; raises RuntimeError when neither reads."""
    if 'level' not in _level:
        from PIL import Image, ImageDraw
        im = Image.new('RGB', (320, 60), 'white')
        ImageDraw.Draw(im).text((10, 20), 'Pick up the bikes', fill='black')
        for level in ('accurate', 'fast'):
            try:
                _text(im, level)
                _level['level'] = level
                break
            except RuntimeError as e:
                error = e
        else:
            raise RuntimeError(f"{error}. If this runs inside an agent's sandbox, such as Codex's, Vision is usually what "
                               "the sandbox blocks: run the reshoot command outside it, with the harness's approval") from None
    return _level['level']


def _perform(im, requests):
    import Vision
    from Foundation import NSData
    b = io.BytesIO()
    im.save(b, "PNG")
    data = b.getvalue()
    handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(NSData.dataWithBytes_length_(data, len(data)), None)
    ok, error = handler.performRequests_error_(requests, None)
    if not ok:
        raise RuntimeError(f"Vision failed ({error.domain() if error else 'unknown'} {error.code() if error else 'unknown'})")


def _text(im, level):
    import Vision
    text = Vision.VNRecognizeTextRequest.alloc().init()
    text.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate if level == 'accurate'
                              else Vision.VNRequestTextRecognitionLevelFast)
    text.setUsesLanguageCorrection_(False)
    _perform(im, [text])
    return text.results() or []


def _vision(im, watch):
    import Vision
    try:
        lines = _text(im, vision_level())
    except RuntimeError:
        if vision_level() == 'fast':
            raise
        _level['level'] = 'fast'  # the accurate reader passed the first try and failed on this image
        lines = _text(im, 'fast')
    faces = Vision.VNDetectFaceRectanglesRequest.alloc().init()
    people = Vision.VNDetectHumanRectanglesRequest.alloc().init()
    if hasattr(people, "setUpperBodyOnly_"):
        people.setUpperBodyOnly_(False)  # whole figures too, such as someone far away
    _perform(im, [faces, people])
    W, H = im.size

    def box(obs):  # Vision's boxes are 0 to 1, from the bottom left
        r = obs.boundingBox()
        return (r.origin.x * W, (1 - r.origin.y - r.size.height) * H, r.size.width * W, r.size.height * H)

    flags = []
    for obs in lines:
        line = obs.topCandidates_(1)[0].string()
        flags += [(box(obs), why, part) for why, part in reasons(line, watch)]
    for obs in faces.results() or []:
        flags.append((box(obs), "a face", f"{obs.confidence():.0%} sure"))
    for obs in people.results() or []:
        if obs.confidence() >= 0.5:
            flags.append((box(obs), "a person", f"{obs.confidence():.0%} sure"))
    return flags


def _tesseract(im, watch):
    b = io.BytesIO()
    im.convert("RGB").save(b, "PNG")
    r = subprocess.run(["tesseract", "stdin", "stdout", "tsv"], input=b.getvalue(), capture_output=True, timeout=60)
    if r.returncode:
        raise RuntimeError("Tesseract failed")
    lines = {}  # (block, paragraph, line): [words, box]
    for row in r.stdout.decode(errors="replace").splitlines()[1:]:
        f = row.split("\t")
        if len(f) < 12 or f[0] != "5" or not f[11].strip():
            continue
        key, (x, y, w, h) = (f[2], f[3], f[4]), map(int, f[6:10])
        words, (x0, y0, x1, y1) = lines.get(key, ([], (x, y, x + w, y + h)))
        lines[key] = (words + [f[11]], (min(x0, x), min(y0, y), max(x1, x + w), max(y1, y + h)))
    flags = []
    for words, (x0, y0, x1, y1) in lines.values():
        flags += [((x0, y0, x1 - x0, y1 - y0), why, part) for why, part in reasons(" ".join(words), watch)]
    return flags
