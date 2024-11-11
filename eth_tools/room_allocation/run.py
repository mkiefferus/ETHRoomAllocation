import os
import json
import datetime
from pathlib import Path
from tabulate import tabulate

import logging
import argparse

# Local imports
from eth_tools.room_allocation.room import Room
from eth_tools.room_allocation.fix_scores import GetLocation
from eth_tools.room_allocation.scraper import (
    download_global_room_info,
    load_global_room_info,
    download_room_allocation,
)

LOGGER = logging.getLogger(__name__)

def run(args):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # ==============
    # Validity check
    # ==============

    VALID_LOCATIONS = GetLocation().locations

    assert args.location in VALID_LOCATIONS, f"Invalid location. Valid locations are: {', '.join(VALID_LOCATIONS)}"

    from_date = (
        datetime.datetime.strptime(args.when, "%Y-%m-%dT%H:%M:%S")
        if args.when
        else datetime.datetime.now()
    )
    
    to_date = from_date + datetime.timedelta(hours=args.duration)

    # ========
    # Init run
    # ========

    room_info_path = Path("data/room_info.json")
    if not os.path.exists(room_info_path):
        LOGGER.debug("Room info file not found. Pulling new one.")
        global_room_info_path = download_global_room_info()
        room_info = load_global_room_info(global_room_info_path)

        for i, room_data in enumerate(room_info["rooms"]):
            LOGGER.info(f"Downloading room {i+1}/{len(room_info['rooms'])}")
            download_room_allocation(
                room=f"{room_data['building']} {room_data['floor']} {room_data['room']}",
                from_date=from_date.date().isoformat(),
                to_date=(from_date.date() + datetime.timedelta(days=7)).isoformat(),
            )
    else:
        LOGGER.debug("Room info file found.")

    # ================
    # Calculate scores
    # ================

    scores = {}
    room_allocations_path = Path("data/room_allocations")
    for room_file in sorted(room_allocations_path.iterdir()):
        if not room_file.suffix == ".json":
            continue

        room = Room(
            room_file, room_info_path
        )
        scores[room.metadata['room']] = room.get_score(
            current_location=args.location, datetime_to=to_date
        )

    # ============
    # Print result
    # ============

    sorted_scores = sorted(scores, key=scores.get, reverse=True)
    if args.top10:
        try:
            table_data = [[room, scores[room]] for room in sorted_scores[:10]]
        except ValueError:
            LOGGER.warning("Less than 10 rooms found.")
            table_data = [[room, scores[room]] for room in sorted_scores]
    else:
        table_data = [[room, scores[room]] for room in sorted_scores[:1]]
    
    print(tabulate(table_data, headers=["Room", "Score"], tablefmt="fancy_grid"))

def main():
    """Run search for best room."""
    parser = argparse.ArgumentParser(
        description="Search script for empty room at ETHZ."
    )
    parser.add_argument(
        "-l",
        "--location",
        type=str,
        required=True,
        help="Location to search room at.",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=int,
        default=4,
        help="Time duration in hours that room should be free.",
    )
    parser.add_argument(
        "--when",
        type=str,
        required=False,
        help="When should room be free. Default is now. Provide under format 'YYYY-MM-DDTHH:MM:SS'.",
    )
    parser.add_argument(
        "--top10",
        action="store_true",
        help="Show top 5 rooms.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )

    run(parser.parse_args())

if __name__ == '__main__':
    main()
