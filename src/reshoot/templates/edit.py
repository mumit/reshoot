"""A basic edit. Customize this or use the cut helpers for more control."""
import sys
from pathlib import Path
from reshoot import cut

source = Path(sys.argv[1])
end = cut.duration(source)
cut.trim(source, 0, end, source.with_name(source.stem + '-final.mp4'))
cut.write_srt(cut.cues(source, 0, end), source.with_name(source.stem + '-final.srt'))
