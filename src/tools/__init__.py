from pathlib import Path

import sys

# Add the file current and the parent dir to the search path for modules.
sys.path.extend(
    str(pobj) for pobj in list(Path(__file__).resolve().parents)[:2])
