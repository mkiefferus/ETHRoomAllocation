import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = Path(os.path.join(BASE_DIR, ".data"))

# Allocations
ROOMS_DIR = Path(os.path.join(DEFAULT_OUTPUT_DIR, "room_allocations"))
ROOM_CONFIG = Path(os.path.join(DEFAULT_OUTPUT_DIR, "room_info.json"))
