import os
import shutil
import datetime
from tabulate import tabulate

import logging
import argparse
import concurrent.futures  # New import for parallelism

# Local imports
from eth_tools.room_allocation.room import Room
from eth_tools.room_allocation.fix_scores import GetLocation
from eth_tools.room_allocation.scraper import (
    download_global_room_info,
    load_global_room_info,
    download_room_allocation,
)

from eth_tools.settings import ROOMS_DIR, ROOM_CONFIG

LOGGER = logging.getLogger(__name__)
MAX_WORKERS = 8

def process_room(i, room_data, from_date, total_rooms):
    """
    Worker function to download room allocation.
    """
    try:
        LOGGER.info(f"Downloading room {i+1}/{total_rooms}")
        download_room_allocation(
            room=f"{room_data['building']} {room_data['floor']} {room_data['room']}",
            from_date=from_date.date().isoformat(),
            to_date=(from_date.date() + datetime.timedelta(days=7)).isoformat(),
        )
    except Exception as e:
        LOGGER.error(f"Failed to download room {i+1}: {e}")


def get_rooms_info(rooms, location, building=None):
    """
    Get rooms info from global room info.
    """
    rooms_info = ([room for room in rooms \
                   if room["location"]["areaDesc"] == location])
    
    if building:
        rooms_info = ([room for room in rooms_info \
                      if room["building"] == building])
        assert rooms_info, f"No rooms found in building {building}. Check building name."

    return rooms_info
        

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
    assert args.top > 1, "Top rooms should be greater than 1."

    from_date = (
        datetime.datetime.strptime(args.when, "%Y-%m-%dT%H:%M:%S")
        if args.when
        else datetime.datetime.now()
    )

    to_date = from_date + datetime.timedelta(hours=args.duration)

    # ========================
    # Ensure data availability
    # ========================

    # Check if desired rooms are present
    if os.path.exists(ROOM_CONFIG) and os.path.exists(ROOMS_DIR) and not args.force_update:
        room_info = load_global_room_info(ROOM_CONFIG)
        
        target_rooms = get_rooms_info(room_info["rooms"], args.location, args.building)
        target_rooms_names = {f"{room['building']}-{room['floor']}-{room['room']}" for room in target_rooms}
        downloaded_rooms = {room.stem for room in ROOMS_DIR.iterdir() if room.suffix == ".json"}

        if target_rooms_names.intersection(downloaded_rooms) != target_rooms_names:
            args.force_update = True
            LOGGER.debug("Not all room files present. Forcing update.")

    # Fetch missing room information
    if not os.path.exists(ROOM_CONFIG) or args.force_update:

        if args.force_update:
            LOGGER.debug("Force update flag set. Pulling new room info.")
        else:
            LOGGER.debug("Room info file not found. Pulling new one.")

        global_room_info_path = download_global_room_info()
        room_info = load_global_room_info(global_room_info_path)

        rooms = get_rooms_info(room_info["rooms"], args.location, args.building)

        total_rooms = len(rooms)

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Prepare futures
            futures = [
                executor.submit(process_room, i, room_data, from_date, total_rooms)
                for i, room_data in enumerate(rooms)
            ]

            # Process as they complete
            for future in concurrent.futures.as_completed(futures):
                future.result()

        LOGGER.info("All room allocations have been processed.")
    else:
        LOGGER.debug("Room info file found.")

    # ================
    # Calculate scores
    # ================

    scores = {}
    for room_file in sorted(ROOMS_DIR.iterdir()):
        if room_file.suffix != ".json":
            continue

        room = Room(room_file, ROOM_CONFIG)

        if room.room_info["location"]["areaDesc"] != args.location:
            continue

        if args.building and room.room_info["building"] != args.building:
            continue

        scores[room.metadata['room']] = room.get_score(
            current_location=args.location, datetime_to=to_date
        )

    # ============
    # Print result
    # ============

    sorted_scores = sorted(scores, key=scores.get, reverse=True)
    try:
        table_data = [[room, scores[room]] for room in sorted_scores[:args.top]]
    except ValueError:
        LOGGER.warning("Less than 10 rooms found.")
        table_data = [[room, scores[room]] for room in sorted_scores]

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
        "--top",
        type=int,
        default=10,
        help="Show n top rooms.",
    )
    parser.add_argument(
        "-b",
        "--building",
        type=str,
        help="Constrain search to building.",
    )
    parser.add_argument(
        "--force_update",
        action="store_true",
        help="Force update room info.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )

    args = parser.parse_args()
    run(args)

if __name__ == '__main__':
    main()
