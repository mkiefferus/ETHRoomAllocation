# app.py
import streamlit as st
import datetime
import logging
import os
from pathlib import Path
import pandas as pd
from zoneinfo import ZoneInfo # Handle streamlit timezone
import concurrent.futures

# Local imports (adjust these as per your project structure)
from eth_tools.room_allocation.room import Room
from eth_tools.room_allocation.fix_scores import GetLocation
from eth_tools.room_allocation.scraper import (
    download_global_room_info,
    load_global_room_info,
    download_room_allocation,
)
from eth_tools.settings import ROOMS_DIR, ROOM_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)
MAX_WORKERS = 8  # Adjust as needed

# Define CET timezone (handles both CET and CEST automatically)
CET = ZoneInfo("Europe/Zurich")

def main():
    st.title("ETHZ Empty Room Finder")

    # Collect user inputs
    locations = GetLocation().locations
    location = st.selectbox("Select Location", options=locations)
    building = st.text_input("Building (optional)")
    duration = st.number_input("Duration in hours", min_value=1, value=4)
    date = st.date_input("Date", value=datetime.date.today())
    
    # Get current CET time
    current_cet_time = datetime.datetime.now(CET).time()
    time = st.time_input("Time", key="time")
    
    top_n = st.number_input("Number of top rooms to display", min_value=1, value=10)
    user_force_update = st.checkbox("Force update room info")

    # When the user clicks the 'Search' button
    if st.button("Search"):
        # Combine date and time into a timezone-aware datetime object
        when = datetime.datetime.combine(date, time).replace(tzinfo=CET)
        # Run the room search
        with st.spinner("Searching for available rooms..."):
            results = run_search(
                location=location,
                duration=duration,
                when=when,
                top=top_n,
                building=building,
                user_force_update=user_force_update
            )
        # Display the results
        if results is not None and not results.empty:
            st.success("Top Available Rooms:")
            st.table(results)
        else:
            st.warning("No rooms found.")

def run_search(location, duration, when, top, building, user_force_update):
    # Validity check
    VALID_LOCATIONS = GetLocation().locations
    if location not in VALID_LOCATIONS:
        st.error(f"Invalid location. Valid locations are: {', '.join(VALID_LOCATIONS)}")
        return None

    if top < 1:
        st.error("Number of top rooms should be greater than 0.")
        return None

    from_date = when
    to_date = from_date + datetime.timedelta(hours=duration)

    # Initialize force_update based on user input
    force_update = user_force_update

    # Ensure data availability
    room_info = None
    if os.path.exists(ROOM_CONFIG) and os.path.exists(ROOMS_DIR) and not force_update:
        room_info = load_global_room_info(ROOM_CONFIG)
        target_rooms = get_rooms_info(room_info["rooms"], location, building)
        target_rooms_names = {f"{room['building']}-{room['floor']}-{room['room']}" for room in target_rooms}
        downloaded_rooms = {room.stem for room in Path(ROOMS_DIR).iterdir() if room.suffix == ".json"}

        missing_rooms = target_rooms_names - downloaded_rooms
        if missing_rooms:
            st.info(f"{len(missing_rooms)} rooms are missing. Updating room information...")
            force_update = True
    else:
        if user_force_update:
            st.info("Force update flag is set. Updating room information...")
        else:
            st.info("Room information not found. Downloading room information...")
        force_update = True

    if force_update:
        try:
            global_room_info_path = download_global_room_info()
            room_info = load_global_room_info(global_room_info_path)
            rooms = get_rooms_info(room_info["rooms"], location, building)
            total_rooms = len(rooms)

            if total_rooms == 0:
                st.warning("No rooms found with the specified criteria.")
                return None

            # Process rooms in parallel
            with st.spinner("Downloading room allocations..."):
                with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = [
                        executor.submit(
                            download_room_allocation,
                            room=f"{room_data['building']} {room_data['floor']} {room_data['room']}",
                            from_date=from_date.date().isoformat(),
                            to_date=(from_date.date() + datetime.timedelta(days=7)).isoformat(),
                        )
                        for room_data in rooms
                    ]

                    progress_bar = st.progress(0)  # Initialize progress bar
                    for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                        try:
                            future.result()
                            progress_bar.progress(i / total_rooms)
                        except Exception as e:
                            LOGGER.error(f"Failed to download room {i}: {e}")
                            st.error(f"Failed to download room {i}: {e}")
                progress_bar.empty()  # Remove progress bar after completion

            st.success("All room allocations have been processed.")
        except Exception as e:
            LOGGER.error(f"Error during room information update: {e}")
            st.error(f"Error during room information update: {e}")
            return None

    # Calculate scores
    scores = {}
    try:
        for room_file in sorted(Path(ROOMS_DIR).iterdir()):
            if room_file.suffix != ".json":
                continue

            room = Room(room_file, ROOM_CONFIG)

            if room.room_info["location"]["areaDesc"] != location:
                continue

            if building and room.room_info["building"] != building:
                continue

            score = room.get_score(current_location=location, datetime_to=to_date)
            scores[room.metadata['room']] = score
    except Exception as e:
        LOGGER.error(f"Error calculating scores: {e}")
        st.error(f"Error calculating scores: {e}")
        return None

    if not scores:
        st.warning("No rooms matched the criteria after processing.")
        return None

    # Sort and prepare the results
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_rooms = sorted_scores[:top] if top <= len(sorted_scores) else sorted_scores
    results = [{"Room": room, "Score": f"{score:.1f}"} for room, score in top_rooms]

    # Convert to DataFrame with custom index starting at 1
    df = pd.DataFrame(results)
    df.index = pd.RangeIndex(start=1, stop=len(df) + 1, step=1)
    df.index.name = "#"

    return df

def get_rooms_info(rooms, location, building=None):
    """
    Get rooms info from global room info.
    """
    rooms_info = [room for room in rooms if room["location"]["areaDesc"] == location]

    if building:
        rooms_info = [room for room in rooms_info if room["building"] == building]
        if not rooms_info:
            st.error(f"No rooms found in building {building}. Check building name.")
            return []
    return rooms_info

if __name__ == '__main__':
    main()
