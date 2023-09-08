import datetime
import os
from turtle import down
from eth_tools.room_allocation.scraper import (
    download_room_allocation,
    load_file_metadata,
    load_global_room_info,
    load_room_allocation,
)


def __midnight_datetime():
    return datetime.datetime.combine(datetime.date.today(), datetime.time.max)


def __now_datetime():
    dt = datetime.datetime.now()
    return datetime.datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0)


def __parse_datetime(date_str):
    # 2023-09-01T08:00:00
    return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


class Room:
    def __init__(self, filepath, room_info_filepath=None):
        self.filepath = filepath
        self.metadata = load_file_metadata(filepath)
        self.allocation = load_room_allocation(filepath)
        self.room_info_filepath = room_info_filepath or os.path.dirname(
            os.path.dirname(self.filepath)
        )
        self.room_info = filter(
            lambda x: f"{x['building']} {x['floor']} {x['room']}" == self.metadata["room"],
            load_global_room_info(room_info_filepath)["rooms"],
        )

    def update_allocation(
        self, datetime_from=__now_datetime(), datetime_to=__midnight_datetime(), force=False
    ):
        download_room_allocation(
            self.metadata["room"],
            date_from=datetime_from.date().isoformat(),
            date_to=(datetime_to.date() + datetime.timedelta(days=7)).isoformat(),  # 7 spare days
            filepath=self.room_info_filepath,
        )
        self.allocation = load_room_allocation(self.filepath)

    def get_slots(self, datetime_from=__now_datetime(), datetime_to=__midnight_datetime()):
        """Returns the slots of the room for the given datetimes

        Args:
            datetime_from (_type_, optional): _description_. Defaults to
                __now_datetime().
            datetime_to (_type_, optional): _description_. Defaults to
                __midnight_datetime().

        Returns:
            list -- List of slots
        """
        # update slots if they are not up to date
        if __parse_datetime(self.allocation[-1]["date_to"]) < datetime_to:
            self.update_allocation(datetime_to=datetime_to)
        # filter slots
        return list(
            filter(
                lambda x: datetime_from <= __parse_datetime(x.get("date_from")) <= datetime_to
                or datetime_from <= __parse_datetime(x.get("date_to")) <= datetime_to,
                self.allocation,
            )
        )

    def get_available_slots(
        self, datetime_from=__now_datetime(), datetime_to=__midnight_datetime()
    ):
        """Returns the available slots of the room for the given datetimes

        belegungstyp: 7 = "frei", 15 = "Studierendenarbeitsplätze"

        Args:
            datetime_from (_type_, optional): _description_. Defaults to
                __now_datetime().
            datetime_to (_type_, optional): _description_. Defaults to
                __midnight_datetime__().
        """
        available_slots = []
        for allocation in self.get_slots(datetime_from, datetime_to):
            belegungsserie = allocation.get("belegungsserie", {})
            belegungstyp = belegungsserie.get("belegungstyp")
            if belegungstyp in [7, 15]:
                available_slots.append(allocation)
        return available_slots

    def is_available(self, datetime_from=__now_datetime(), datetime_to=__midnight_datetime()):
        """Checks if the room is fully available for the given datetimes"""
        return len(self.get_slots(datetime_from, datetime_to)) == len(
            self.get_available_slots(datetime_from, datetime_to)
        )

    def get_score(self, datetime_from=__now_datetime(), datetime_to=__midnight_datetime()):
        pass

    def download_allocation(
        self,
        date_from=datetime.date.today().isoformat(),
        date_to=(datetime.date.today() + datetime.timedelta(days=7)).isoformat(),
    ):
        download_room_allocation(
            self.metadata["room"],
            date_from=date_from,
            date_to=date_to,
            filepath=self.room_info_filepath,
        )
