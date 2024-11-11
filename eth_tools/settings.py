import os
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path(".data")

# Allocations
ROOMS_DIR = Path(os.path.join(DEFAULT_OUTPUT_DIR, "room_allocations"))
ROOM_CONFIG = Path(os.path.join(DEFAULT_OUTPUT_DIR, "room_info.json"))
