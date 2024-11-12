import datetime
import os
import numpy as np
from zoneinfo import ZoneInfo

CET = ZoneInfo("Europe/Zurich")

# Local imports
from eth_tools.room_allocation.scraper import (
    download_room_allocation,
    load_file_metadata,
    load_global_room_info,
    load_room_allocation,
)

from eth_tools.room_allocation.fix_scores import GetLocation, GetTypeScore

get_location = GetLocation()
get_type_score = GetTypeScore()

def _midnight_datetime():
    naive_dt = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
    return naive_dt.replace(tzinfo=CET)

def _now_datetime():
    return datetime.datetime.now(CET).replace(minute=0, second=0, microsecond=0)


def _parse_datetime(date_str):
    # 2023-09-01T08:00:00
    naive_dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    return naive_dt.replace(tzinfo=CET)


class Room:
    def __init__(self, filepath, room_info_filepath=None):
        self.filepath = filepath
        self.metadata = load_file_metadata(filepath)
        self.allocation = load_room_allocation(filepath)
        self.room_info_filepath = room_info_filepath or os.path.dirname(
            os.path.dirname(self.filepath)
        )
        self.room_info = next(filter(
            lambda x: f"{x['building']} {x['floor']} {x['room']}" == self.metadata["room"],
            load_global_room_info(room_info_filepath)["rooms"],
        ))

    def update_allocation(
        self, datetime_from=_now_datetime(), datetime_to=_midnight_datetime(), force=False
    ):
        download_room_allocation(
            self.metadata["room"],
            date_from=datetime_from.date().isoformat(),
            date_to=(datetime_to.date() + datetime.timedelta(days=7)).isoformat(),  # 7 spare days
            filepath=self.room_info_filepath,
        )
        self.allocation = load_room_allocation(self.filepath)

    def get_slots(self, datetime_from=_now_datetime(), datetime_to=_midnight_datetime()):
        """Returns the slots of the room for the given datetimes

        Args:
            datetime_from (_type_, optional): _description_. Defaults to
                _now_datetime().
            datetime_to (_type_, optional): _description_. Defaults to
                _midnight_datetime().

        Returns:
            list -- List of slots
        """
        # TODO: handle empty allocation (no allocation = prob. not open room)
        if not self.allocation:
            return []
        # update slots if they are not up to date
        elif _parse_datetime(self.allocation[-1]["date_to"]) < datetime_to:
            self.update_allocation(datetime_to=datetime_to)
        # filter slots
        return list(
            filter(
                lambda x: _parse_datetime(x.get("date_from")) <= datetime_to and
                          _parse_datetime(x.get("date_to")) >= datetime_from,
                self.allocation,
            )
        )

    def get_available_slots(
        self, datetime_from=_now_datetime(), datetime_to=_midnight_datetime()
    ):
        """Returns the available slots of the room for the given datetimes

        belegungstyp: 7 = "frei", 15 = "Studierendenarbeitsplätze"

        Args:
            datetime_from (_type_, optional): _description_. Defaults to
                _now_datetime().
            datetime_to (_type_, optional): _description_. Defaults to
                _midnight_datetime__().
        """
        available_slots = []
        for allocation in self.get_slots(datetime_from, datetime_to):
            belegungsserie = allocation.get("belegungsserie", {})
            belegungstyp = belegungsserie.get("belegungstyp")
            if belegungstyp in [7, 15]:
                available_slots.append(allocation)
        return available_slots

    def is_available(self, datetime_from=_now_datetime(), datetime_to=_midnight_datetime()):
        """Checks if the room is fully available for the given datetimes"""
        return len(self.get_slots(datetime_from, datetime_to)) == len(
            self.get_available_slots(datetime_from, datetime_to)
        )
    
    def get_previous_slots(self, datetime_from=_now_datetime()):
        """Returns previous slots of the room for the same day
        
        Args:
            datetime_from (_type_, optional): _description_: Current timestamp. Defaults to
                _now_datetime().
        """
        ignore_slot_type = [8] # 8 = "geschlossen"

        previous_slots = self.get_slots(datetime_from.replace(hour=0, minute=0, second=0), 
                                        datetime_from)
        return list(filter(lambda x: x.get("belegungsserie", {}).get("belegungstyp") 
                           not in ignore_slot_type, previous_slots))
    
    
    def get_delta_to_next_slot(self, datetime_from=_now_datetime()):
        """Returns the time delta to the next slot
        
        Args:
            datetime_from (_type_, optional): _description_: Current timestamp. Defaults to
                _now_datetime().
        """
        evening = datetime_from.replace(hour=22, minute=00, second=00) # Many rooms close at 22:00

        next_slots = self.get_slots(datetime_from, evening)
        next_slot = next_slots[0] if next_slots else None

        if not next_slot:
            return evening - datetime_from
        else:
            return _parse_datetime(next_slot["date_from"]) - datetime_from
    
    def get_distance_to_location(self, current_location):
        """Returns distance of room to current location."""
        return get_location(current_location, self.room_info["location"]['areaDesc'])

    def get_score(self, current_location, datetime_from=_now_datetime(), datetime_to=_midnight_datetime()):
        """Returns the score of the room for the given datetimes"""

        scores = []
        scores_weights = []
        
        # 1. Is room available?
        scores.append(100*self.is_available(datetime_from, datetime_to))
        scores_weights.append(0.51)
        
        # 2. Distance to location
        scores.append(-self.get_distance_to_location(current_location))
        scores_weights.append(0.15)

        # 3. Has room been used before?
        previous_slots = self.get_previous_slots(datetime_from)
        scores.append(100 if previous_slots else 0)
        scores_weights.append(0.11)

        # 4. Room type (e.g. prioritise seminar room over lecture hall)
        scores.append(get_type_score(self.room_info["type"]))
        scores_weights.append(0.09)

        # 5. Time to next slot (4 hours before next slot yield max points)
        delta = self.get_delta_to_next_slot(datetime_from).seconds // 60
        scores.append(np.clip(100 - (4*60 - delta), 0, 100))
        scores_weights.append(0.09)

        # 6. Room capacity - Larger rooms attract more people
        number_of_seats = int(self.room_info.get("seats", 0))
        scores.append(np.clip(100 - number_of_seats, 0, 100))
        scores_weights.append(0.05)

        # details = f"""
        # Room {self.metadata["room"]}:
        # - Available: {scores[0]:.2f} * {scores_weights[0]:.2f} = {scores[0]*scores_weights[0]:.2f}
        # - Distance: -{scores[1]:.2f} * {scores_weights[1]:.2f} = -{scores[1]*scores_weights[1]:.2f}
        # - Previous usage: {scores[2]:.2f} * {scores_weights[2]:.2f} = {scores[2]*scores_weights[2]:.2f}
        # - Room type: {scores[3]:.2f} * {scores_weights[3]:.2f} = {scores[3]*scores_weights[3]:.2f}
        # - Time to next slot: {scores[4]:.2f} * {scores_weights[4]:.2f} = {scores[4]*scores_weights[4]:.2f}
        # - # Seats: {scores[5]:.2f} * {scores_weights[5]:.2f} = {scores[5]*scores_weights[5]:.2f}
        
        # Total score: {np.dot(scores, scores_weights):.2f}
        # """

        return np.dot(scores, scores_weights)
    
    # def get_score(self, current_location, datetime_from=_now_datetime(), datetime_to=_midnight_datetime()):
    #     """Returns the score of the room for the given datetimes"""
    #     score, _ = self.get_detailed_score(current_location, datetime_from, datetime_to)
    #     return score

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
