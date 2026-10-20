"""Puts everything a take could show on numbered sheets, to check by eye before anything is shared.

    reshoot check web.assets.json web.mp4 shots/      # sheets of what isn't checked yet
    reshoot check --fail 3-2 7-1                       # these failed: lists where they came from
    reshoot check --ok                                 # every other photo on the sheets passed

Sources can be image files, folders of them, image URLs, the .assets.json lists `reshoot web` writes, or videos (a
frame every few seconds, --every). Sheets go to the review folder (default review/), four images each at up to
1000 px, labelled like 3-2. `--ok` records each passed image by a hash of its bytes in checked.json, so a later take
only shows what's new. A frame of a new take is always new, so take frames are checked each time.

Each image is also scanned (scan.py) for text that looks private (emails, phone numbers, keys, file paths with a
user name, street addresses, and the words given with --watch-for) and for faces and people. What it finds is boxed
in red on the sheets, which put flagged images first, and listed with what was found masked, so a key doesn't end
up in a log. The scan points at problems; it never passes an image.
"""
import hashlib, io, json, mimetypes, platform, subprocess, tempfile, urllib.request, uuid
from reshoot.safety import describe
from datetime import date
from pathlib import Path

IMAGES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic"}
VIDEOS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


def load(p, default):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else default


def items(sources, every=3):
    """(where it came from, image bytes) for each image the sources name."""
    for s in sources:
        p = Path(s)
        if s.startswith(("http://", "https://")):
            try:
                yield s, urllib.request.urlopen(s, timeout=30).read()
            except OSError as e:
                raise ValueError(f"cannot fetch {describe(s)} ({type(e).__name__})") from None
        elif p.suffix == ".json":
            try:
                sources = json.loads(p.read_text())
                if not isinstance(sources, list) or not all(isinstance(x, str) for x in sources):
                    raise ValueError()
            except (OSError, ValueError):
                raise ValueError(f"invalid or missing source list: {describe(s)}") from None
            yield from items(sources, every)
        elif p.is_dir():
            yield from items(sorted(str(f) for f in p.rglob("*") if f.suffix.lower() in IMAGES | VIDEOS), every)
        elif p.suffix.lower() in VIDEOS:
            with tempfile.TemporaryDirectory() as t:
                subprocess.run(["ffmpeg", "-loglevel", "error", "-i", s, "-vf", f"fps=1/{every}", f"{t}/%05d.jpg"], check=True, capture_output=True)
                for i, f in enumerate(sorted(Path(t).glob("*.jpg"))):
                    yield f"{s}@{i * every}s", f.read_bytes()
        elif p.exists():
            yield s, p.read_bytes()
        else:
            raise ValueError(f"missing source: {describe(s)}")


def open_image(data):
    from PIL import Image, ImageOps
    try:
        im = Image.open(io.BytesIO(data))
    except Exception:
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
            im = Image.open(io.BytesIO(data))
        except Exception:
            return None
    return ImageOps.exif_transpose(im).convert("RGB")


def mask(why, part):
    """Enough of what was found to recognise it, not enough to use it. A face or a person has only how sure the scan
    is, which isn't private."""
    if why in ("a face", "a person"):
        return f"({part})"
    return part[:4] + "•••" if len(part) > 6 else "•••"


def sheets(todo, review):
    """Numbered sheets of the images, four at a time, flagged ones first; returns {label: [source, hash]} and writes
    flags.json, {label: [[reason, masked], ...]}."""
    from PIL import Image, ImageDraw
    todo = sorted(todo, key=lambda t: not t[3])  # flagged first, otherwise in order
    for old in [*review.glob("*.jpg"), review / "failed.json", review / "flags.json"]:
        old.unlink(missing_ok=True)
    review.mkdir(parents=True, exist_ok=True)
    key, flagged = {}, {}
    for s in range(0, len(todo), 4):
        sheet = Image.new("RGB", (2 * 1010, 2 * 790), "white")
        d = ImageDraw.Draw(sheet)
        for j, (src, h, im, flags) in enumerate(todo[s:s + 4]):
            full = im.size
            im.thumbnail((1000, 750))
            k = im.size[0] / full[0]
            x, y, label = (j % 2) * 1010, (j // 2) * 790, f"{s // 4 + 1}-{j + 1}"
            sheet.paste(im, (x, y + 34))
            for (bx, by, bw, bh), _, _ in flags:  # a red box round each thing the scan found
                d.rectangle((x + bx * k - 3, y + 34 + by * k - 3, x + (bx + bw) * k + 3, y + 34 + (by + bh) * k + 3),
                            outline=(230, 30, 30), width=3)
            d.rectangle((x, y, x + 70, y + 30), fill=(200, 20, 20) if flags else "black")
            d.text((x + 8, y + 8), label + (" !" if flags else ""), fill="white")
            key[label] = [describe(src), h]
            if flags:
                flagged[label] = [[why, mask(why, part)] for _, why, part in flags]
        sheet.save(review / f"{s // 4 + 1:02}.jpg", quality=92)
    (review / "key.json").write_text(json.dumps(key, indent=1))
    (review / "flags.json").write_text(json.dumps(flagged, indent=1, ensure_ascii=False))
    return key, flagged


def perform(a, report):
    review = Path(a.review)
    checked = load(review / "checked.json", {})
    if a.fail:
        key = load(review / "key.json", {})
        bad = [key[l] for l in a.fail if l in key]
        if missing := [l for l in a.fail if l not in key]:
            raise SystemExit(f"not on the current sheets: {' '.join(missing)}")
        failed = load(review / "failed.json", [])
        (review / "failed.json").write_text(json.dumps(sorted({h for _, h in bad} | set(failed)), indent=1))
        print("failed. Take these out of the demo data, then record the take again:")
        for src, _ in bad:
            print("  " + src)
        return 0
    if a.ok:
        if not (review / "key.json").exists():
            raise ValueError("no current review sheets")
        if load(review / "report.json", {}).get("status") == "error":
            raise ValueError("the check failed: fix its inputs and run it again before accepting")
        key, failed = load(review / "key.json", {}), set(load(review / "failed.json", []))
        passed = {h: src for src, h in key.values() if h not in failed}
        checked |= {h: {"source": src, "checked": date.today().isoformat()} for h, src in passed.items()}
        (review / "checked.json").write_text(json.dumps(checked, indent=1, sort_keys=True))
        print(f"{len(passed)} more checked ({len(checked)} in all), {len(failed)} failed")
        return 0
    from reshoot import scan
    watch = [w.strip() for arg in a.watch_for or [] for w in
             (Path(arg[1:]).read_text().splitlines() if arg.startswith("@") else arg.split(","))]
    can = scan.can_scan() if a.scan else set()
    mac = platform.system() == "Darwin"
    if a.scan and mac and "people" not in can:  # on a Mac, Vision does it all, but it's a separate package
        print("  no scan: Vision isn't installed with this reshoot. Reinstall it (uv tool install --force "
              "git+https://github.com/mumit/reshoot) or add pyobjc-framework-Vision. Until then, look closely")
    elif a.scan and "text" not in can:
        print("  no text scan: install Tesseract (apt install tesseract-ocr), or look closely")
    if a.scan and not mac:
        print("  no scan for faces and people here (it needs macOS): look for them yourself")
    report['scan'] = {'status': 'completed' if can else 'skipped', 'detectors': sorted(can),
                      'people': 'available' if 'people' in can else 'unavailable',
                      'mode': 'sampled', 'every': a.every}
    if a.scan and 'text' not in can:
        raise ValueError("required text scan unavailable: install Vision or Tesseract, or explicitly use --no-scan")
    if not a.sources:
        raise ValueError("give at least one review source")
    if a.every <= 0:
        raise ValueError("--every must be positive")
    todo, seen = [], set()
    for src, data in items(a.sources, a.every):
        report["samples"] += 1
        h = hashlib.sha256(data).hexdigest()[:16]
        if h in checked or h in seen:
            continue
        seen.add(h)
        im = open_image(data)
        if im is None:
            raise ValueError(f"cannot decode image: {describe(src)}")
        todo.append((src, h, im, scan.scan(im, watch) if can else []))
    if not todo:
        print("all supplied images and sampled frames have been reviewed; unsampled frames are not covered")
        report.update(unchecked=0, flagged=0, review="completed")
        return 0
    key, flagged = sheets(todo, review)
    report.update(unchecked=len(key), flagged=len(flagged), review="pending")
    if flagged:
        print(f"The scan flagged {len(flagged)} of them (boxed in red, on the first sheets). Look at these first:")
        for label, flags in flagged.items():
            print(f"  {label}  {key[label][0]}: " + "; ".join(f"{why} {part}" for why, part in flags))
    print(f"{len(todo)} images not checked yet, on {(len(todo) + 3) // 4} sheets in {review}/. Look at each one "
          "at full size, then run `reshoot check --fail LABEL...` for any that fail and `reshoot check --ok`.")
    return 1


def main(a):
    review = Path(a.review)
    review.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "id": str(uuid.uuid4()), "status": "running",
              "scan": {"status": "pending"}, "review": "pending", "samples": 0,
              "unchecked": None, "flagged": None, "errors": []}
    try:
        code = perform(a, report)
        report['status'] = 'completed'
        if a.ok or a.fail:
            previous = load(review / 'report.json', {})
            if previous:
                report = previous
                report['review'] = 'failed' if load(review / 'failed.json', []) else 'completed'
        return code
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError) as e:
        from reshoot.safety import redact
        message = redact(str(e)) if not isinstance(e, subprocess.SubprocessError) else 'frame decoder failed'
        report.update(status='error', errors=[message])
        report['scan']['status'] = 'failed'
        print('check failed: ' + message)
        return 2
    finally:
        (review / 'report.json').write_text(json.dumps(report, indent=2))
