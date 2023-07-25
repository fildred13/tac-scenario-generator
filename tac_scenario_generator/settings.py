import os
import pathlib

# TODO: pretty sure this isn't portable, but whatever I can fix that later.
SCREENSHOTS_DIR = os.getenv('TSG_SCREENSHOTS_DIR', pathlib.Path(os.getcwd()) / 'screenshots')

SUPPORTED_FORCES = [
    'heer'
]
