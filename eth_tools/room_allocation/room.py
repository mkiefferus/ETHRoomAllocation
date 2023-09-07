from eth_tools.room_allocation.scraper import load_file_metadata, load_room_allocation


class Room:
    def __init__(self, filepath):
        self.filepath = filepath
        self.metadata = load_file_metadata(filepath)
        self.allocation = load_room_allocation(filepath)
        # TODO : if room doesn't have new date - download new allocation

    def is_available(self, datetime_from, datetime_to):
        # TODO : check if room is available
        pass

    def get_available_slots(self, datetime_from, datetime_to):
        # TODO : return list of available dates
        pass

    def get_score(self, datetime_from, datetime_tp):
        # TODO : return score of room for given dates
        pass

    def download_allocation(self, date_from, date_to):
        # TODO : download new allocation
        pass
