"""
Scraper for ETHZ room allocation data.
1. Download the global room info
2. Download the room allocation of a given room and date range
3. Load the room allocation from a given file
4. Load the room allocations from a given directory
"""
import json
import logging
import os
from typing import Any, Optional
from urllib import parse
from datetime import date

# from anyio import key


from eth_tools.eth_requests.session import ETHSession
from eth_tools.settings import ROOMS_DIR, ROOM_CONFIG

ROOM_GLOBAL_INFO = "https://ethz.ch/bin/ethz/roominfo?path=/rooms&lang=en"
ROOM_ALLOCATION_BASE = "https://ethz.ch/bin/ethz/roominfo?path=/rooms/"

session = ETHSession()


def _get_allocation_url(room: str, from_date: str, to_date: str) -> str:
    """Returns the url for the room allocation of the given room and date range

    Arguments:
        room {str} -- Room name in format BUILDING FLOOR ROOM
        from_date {str} -- Start date in format YYYY-MM-DD
        to_date {str} -- End date in format YYYY-MM-DD

    Returns:
        str -- URL for the room allocation of the given room and date range
    """
    return (
        ROOM_ALLOCATION_BASE
        + parse.quote(room)
        + "/allocations"
        + "&from="
        + from_date
        + "&to="
        + to_date
    )


def _get_filepath(room: str, output_dir: str) -> str:
    """Returns the filepath for the room allocation of the given room

    Arguments:
        room {str} -- Room name in format BUILDING FLOOR ROOM

    Returns:
        str -- Filepath for the room allocation of the given room
    """
    return os.path.join(output_dir, f"{'-'.join(room.split())}.json")


def download_json(
    url: str,
    filepath: str,
    metadata: Optional[dict] = None,
    transform_response: Optional[Any] = None,
) -> str:
    """Downloads the content of the given url

    Arguments:
        url {str} -- URL to download
        filepath {str} -- Path to output file
        metadata {dict} -- Metadata to add to the response
        transform_response {Any} -- Function to transform the response

    Returns:
        str -- path to output file
    """
    res = session.get(url)
    res.raise_for_status()
    res_obj = res.json()
    if transform_response is not None:
        res_obj = transform_response(res_obj)
    if metadata is not None:
        if res_obj.get("metadata") is not None:
            logging.warning("Overwriting response metadata field for %s", filepath)
        res_obj["metadata"] = metadata
    with open(filepath, "w") as f:
        json.dump(res_obj, f, indent=4)
    return filepath


def download_room_allocation(
    room: str,
    from_date: str,
    to_date: str,
    output_dir: str = ROOMS_DIR,
    filepath=None,
):
    """Downloads the room allocation of the given room and date range

    Arguments:
        room {str} -- Room name in format BUILDING FLOOR ROOM
        from_date {str} -- Start date in format YYYY-MM-DD
        to_date {str} -- End date in format YYYY-MM-DD

    Returns:
        str -- Room allocation of the given room and date range
    """
    assert room.count(" ") == 2, "Room name must be in format BUILDING FLOOR ROOM"
    os.makedirs(output_dir) if not os.path.exists(output_dir) else 1
    filepath = filepath or _get_filepath(room, output_dir)
    metadata = dict(room=room, from_date=from_date, to_date=to_date)
    return download_json(
        _get_allocation_url(room, from_date, to_date),
        filepath,
        transform_response=lambda x: dict(room_allocation=x),
        metadata=metadata,
    )


def download_global_room_info(
    output_path:str = ROOM_CONFIG,
) -> str:
    """Downloads the global room info

    Keyword Arguments:
        output_dir {str} -- Output directory (default: {DEFAULT_OUTPUT_DIR})
        output_name {str} -- Output filename (default: {"room_info.json"})

    Returns:
        str -- Path to output file
    """
    os.makedirs(os.path.dirname(output_path)) if not os.path.exists(os.path.dirname(output_path)) else 1
    return download_json(
        ROOM_GLOBAL_INFO,
        filepath=ROOM_CONFIG,
        metadata=dict(ts=date.today().isoformat()),
        transform_response=lambda x: dict(rooms=x),
    )


def load_file_metadata(filepath):
    """Returns the metadata of the given file

    Arguments:
        filepath {str} -- Path to file

    Returns:
        dict -- Metadata of the given file
    """
    with open(filepath) as f:
        return json.load(f)["metadata"]


def load_global_room_info(
    filepath: str = ROOM_CONFIG,
) -> dict:
    """Loads the room info from the given file

    Keyword Arguments:
        filepath {str} -- Path to file (default:
            {os.path.join(DEFAULT_OUTPUT_DIR, "room_info.json")})

    Returns:
        dict -- Room info from the given file
    """
    with open(filepath, "r") as fh:
        return json.load(fh)


def load_room_allocation(
    filepath: str,
) -> dict:
    """
    Loads the room allocation from the given file

    Returns:
        dict -- Room allocation from the given file
    """
    with open(filepath, "r") as fh:
        room_allocation = json.load(fh)["room_allocation"]
    
    return room_allocation.sort(key=lambda x: x["date_to"])


def load_room_allocations(
    directory: str = ROOMS_DIR, as_dict=False
) -> dict:
    """
    Loads the room allocations from the given directory

    Returns:
        dict or list -- Room allocations from all the files in the given directory
    """
    room_allocations = {} if as_dict else []
    for filename in os.listdir(directory):
        if as_dict:
            room_allocations[filename] = load_room_allocation(os.path.join(directory, filename))
        else:
            room_allocations.append(load_room_allocation(os.path.join(directory, filename)))
    return room_allocations
