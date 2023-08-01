import os
import pathlib

# TODO: pretty sure these aren't portable, but whatever I can fix that later.
DEBUG_DIR = os.getenv('TSG_DEBUG_DIR', pathlib.Path(os.getcwd()) / 'debug')
SCREENSHOTS_DIR = DEBUG_DIR / 'screenshots'
