"""Main module for the scraper"""
from urllib import parse


ROOM_GLOBAL_INFO = "https://ethz.ch/bin/ethz/roominfo?path=/rooms&lang=en"
ROOM_ALLOCATION_BASE = "https://ethz.ch/bin/ethz/roominfo?path=/rooms/"


def allocation_url(room, from_date, to_date):
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
