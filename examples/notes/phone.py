"""The notes example on a phone: the same beats at 390 x 844, an iPhone's size."""
import runpy
from pathlib import Path

URL = "http://localhost:8000/"
SIZE = "390x844@3"
MOBILE = True
BEATS = runpy.run_path(str(Path(__file__).with_name("storyboard.py")))["BEATS"]
