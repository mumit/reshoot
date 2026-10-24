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
import hashlib, io, json, mimetypes, os, platform, subprocess, tempfile, urllib.request, uuid
from reshoot.safety import describe
from datetime import date
from pathlib import Path

IMAGES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic"}
VIDEOS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


def load(p, default):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else default


def items(sources, every=3, full=False):
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
            yield from items(sources, every, full)
        elif p.is_dir():
            yield from items(sorted(str(f) for f in p.rglob("*") if f.suffix.lower() in IMAGES | VIDEOS), every, full)
        elif p.suffix.lower() in VIDEOS and full:
            yield from video_frames(s)
        elif p.suffix.lower() in VIDEOS:
            next_at = 0
            for source, data in video_frames(s):
                at = float(source.rsplit('@', 1)[1][:-1])
                if at + 1e-6 >= next_at:
                    yield source, data
                    next_at = at + every
        elif p.suffix.lower() == '.gif':
            from PIL import Image, ImageSequence
            at, next_at = 0, 0
            with Image.open(p) as gif:
                for frame in ImageSequence.Iterator(gif):
                    buffer = io.BytesIO()
                    frame.convert('RGB').save(buffer, 'PNG')
                    if full or at + 1e-6 >= next_at:
                        yield f'{s}@{at:.3f}s', buffer.getvalue()
                        next_at = at + every
                    at += frame.info.get('duration', 100) / 1000
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
            if isinstance(im, Path):
                im = Image.open(im).convert("RGB")
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



def text_findings(paths, watch, checked, policy):
    """Scan supplied words directly, without relying on OCR of rendered captions."""
    from reshoot.scan import reasons
    key, flags = {}, {}
    for source in paths:
        path = Path(source)
        text = path.read_text()
        if path.suffix == '.srt':
            import re
            blocks = re.split(r'\n\s*\n', text.strip()) if text.strip() else []
            entries = []
            for block in blocks:
                lines = block.splitlines()
                if len(lines) < 3 or ' --> ' not in lines[1]:
                    raise ValueError('invalid subtitle text input')
                entries.append((lines[1], '\n'.join(lines[2:])))
        elif path.name.endswith('.voice.json'):
            entries = [(str(row['t']) + 's', row['text']) for row in json.loads(text)]
        else:
            raise ValueError('text inputs must be .srt or .voice.json')
        for location, words in entries:
            found = reasons(words, watch)
            h = hashlib.sha256((str(path.resolve()) + text + location).encode()).hexdigest()[:16]
            if found and not (h in checked and checked[h].get('policy') == policy):
                label = 'text-' + str(len(key)+1)
                key[label] = [describe(source) + ' at ' + location, h]
                flags[label] = [[why, mask(why, part)] for why, part in found]
    return key, flags


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
        policy = load(review / 'report.json', {}).get('policy')
        checked |= {h: {"source": src, "checked": date.today().isoformat(), 'policy': policy} for h, src in passed.items()}
        (review / "checked.json").write_text(json.dumps(checked, indent=1, sort_keys=True))
        print(f"{len(passed)} more checked ({len(checked)} in all), {len(failed)} failed")
        return 0
    from reshoot import scan
    watch = [w.strip() for arg in a.watch_for or [] for w in
             (Path(arg[1:]).read_text().splitlines() if arg.startswith("@") else arg.split(","))]
    engine = getattr(a, 'ocr', None)
    can = (scan.can_scan(engine) if engine else scan.can_scan()) if a.scan else set()
    mac = platform.system() == "Darwin"
    if a.scan and 'people' not in can:
        print('  face and person detection unavailable with this backend; inspect those by eye')
    report['scan'] = {'status': 'completed' if can else 'skipped', 'detectors': sorted(can),
                      'people': 'available' if 'people' in can else 'unavailable',
                      'mode': 'full' if getattr(a, 'full', False) else 'sampled', 'every': None if getattr(a, 'full', False) else a.every}
    if a.scan and 'text' not in can:
        raise ValueError("required text scan unavailable: install Vision or Tesseract, or explicitly use --no-scan")
    if not a.sources:
        raise ValueError("give at least one review source")
    if a.every <= 0:
        raise ValueError("--every must be positive")
    from importlib.metadata import version
    report['scan']['backend'] = scan.backend(engine) if a.scan else 'disabled'
    report['scan']['engine_version'] = platform.mac_ver()[0] if scan.backend(engine) == 'vision' else (subprocess.run(['tesseract', '--version'], capture_output=True, text=True).stdout.splitlines()[0] if can else 'unavailable')
    report['scan']['rules_version'] = version('reshoot')
    report['policy'] = hashlib.sha256(json.dumps({'watch': watch, 'scan': report['scan'], 'rules': scan.PATTERNS.__repr__()}, sort_keys=True).encode()).hexdigest()
    originals = review / 'originals'
    originals.mkdir(exist_ok=True)
    file_hashes = {}
    todo, seen = [], set()
    for src, data in items(a.sources, a.every, getattr(a, 'full', False)):
        report["samples"] += 1
        origin = src.rsplit('@', 1)[0]
        identity = b''
        if Path(origin).suffix.lower() in VIDEOS | {'.gif'} and Path(origin).is_file():
            from reshoot.artifacts import digest
            if origin not in file_hashes:
                file_hashes[origin] = digest(origin)
            identity = (origin + file_hashes[origin]).encode()
        h = hashlib.sha256(identity + data).hexdigest()[:16]
        if (h in checked and checked[h].get('policy') == report['policy']) or h in seen:
            continue
        seen.add(h)
        im = open_image(data)
        if im is None:
            raise ValueError(f"cannot decode image: {describe(src)}")
        flags = scan.scan(im, watch, engine) if can else []
        original = originals / (h + '.png')
        im.save(original)
        todo.append((src, h, original, flags))
    if not report['samples']:
        raise ValueError('sources contained no reviewable frames or images')
    text_paths = getattr(a, 'text_file', []) if a.scan else []
    text_key, text_flags = text_findings(text_paths, watch, checked, report['policy'])
    report['scan']['text_files'] = len(text_paths)
    if not todo and not text_key:
        print("all supplied images and sampled frames have been reviewed; unsampled frames are not covered")
        report.update(unchecked=0, flagged=0, review="completed")
        return 0
    key, flagged = sheets(todo, review)
    key.update(text_key)
    flagged.update(text_flags)
    (review / 'key.json').write_text(json.dumps(key, indent=1))
    (review / 'flags.json').write_text(json.dumps(flagged, indent=1, ensure_ascii=False))
    report.update(unchecked=len(key), flagged=len(flagged), review="pending")
    if flagged:
        print(f"The scan flagged {len(flagged)} of them (boxed in red, on the first sheets). Look at these first:")
        for label, flags in flagged.items():
            print(f"  {label}  {key[label][0]}: " + "; ".join(f"{why} {part}" for why, part in flags))
    if os.environ.get('RESHOOT_IN_RUN'):  # the run says what to do next
        print(f"{len(key)} scan items on {(len(todo) + 3) // 4} sheets, in the run's review/ folder.")
        return 1
    print(f"{len(key)} frames, images, or text findings not checked yet, on {(len(todo) + 3) // 4} sheets in {review}/. Look at each one "
          "at full size. For a run, record the verdict with `reshoot accept RUN`; for these sheets alone, run "
          "`reshoot check --fail LABEL...` for any that fail and `reshoot check --ok`.")
    return 1


def main(a):
    review = Path(a.review)
    review.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "id": str(uuid.uuid4()), "status": "running",
              "scan": {"status": "pending"}, "review": "pending", "samples": 0,
              "unchecked": None, "flagged": None, "errors": []}
    if not (a.ok or a.fail):
        (review / 'report.json').write_text(json.dumps(report, indent=2))
    try:
        code = perform(a, report)
        report['status'] = 'completed'
        if a.ok or a.fail:
            previous = load(review / 'report.json', {})
            if previous:
                report = previous
                report['review'] = 'failed' if load(review / 'failed.json', []) else 'completed'
        return code
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError, KeyboardInterrupt) as e:
        from reshoot.safety import redact
        message = redact(str(e)) if not isinstance(e, subprocess.SubprocessError) else 'frame decoder failed'
        report.update(status='error', errors=[message])
        report['scan']['status'] = 'failed'
        print('check failed: ' + message)
        return 2
    finally:
        (review / 'report.json').write_text(json.dumps(report, indent=2))


def video_frames(source):
    """Decode every frame and pair it with its original presentation time."""
    decoder = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', source, '-fps_mode', 'passthrough', '-f', 'image2pipe', '-vcodec', 'ppm', '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    probe = subprocess.Popen(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_frames', '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'csv=p=0', source], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    count = 0
    try:
        while header := decoder.stdout.readline():
            if header != b'P6\n':
                raise ValueError('unexpected decoded frame format')
            size = decoder.stdout.readline()
            maximum = decoder.stdout.readline()
            width, height = map(int, size.split())
            if maximum.strip() != b'255' or width <= 0 or height <= 0:
                raise ValueError('invalid decoded frame')
            wanted = width * height * 3
            data = bytearray()
            while len(data) < wanted:
                part = decoder.stdout.read(wanted - len(data))
                if not part:
                    raise ValueError('incomplete decoded frame')
                data.extend(part)
            while True:
                line = probe.stdout.readline()
                if not line:
                    raise ValueError('frame timestamps unavailable')
                try:
                    at = float(line.split(b',')[0])
                    break
                except ValueError:
                    continue
            count += 1
            yield f'{source}@{at:.6f}s', header + size + maximum + data
        if decoder.wait() or probe.wait() or not count:
            raise ValueError('frame decoding failed')
    finally:
        for proc in (decoder, probe):
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            proc.stdout.close()
