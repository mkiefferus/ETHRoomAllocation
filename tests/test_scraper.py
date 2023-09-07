# flake8: noqa: C0116,W0611

import os
from pathlib import Path
from random import randint
import shutil
import pytest

from datetime import date
from eth_tools.room_allocation.scraper import _get_allocation_url, _get_filepath
from eth_tools.room_allocation.scraper import (
    download_json,
    download_room_allocation,
    load_file_metadata,
    download_global_room_info,
    load_room_allocation,
    load_room_allocations)

TEST_BASE_OUTPUT_DIR = f"test_data_{randint(100, 999):3d}"
TEST_OUTPUT_DIR = os.path.join(TEST_BASE_OUTPUT_DIR, "room_allocations")
TEST_OUTPUT_NAME = "room_info.json"
TEST_OUTPUT_FILEPATH = os.path.join(TEST_OUTPUT_DIR, TEST_OUTPUT_NAME)
TEST_ROOM = "HPH G 1"
TEST_ROOM_FILEPATH = os.path.join(TEST_OUTPUT_DIR, "-".join(TEST_ROOM.split()) + ".json")


def setup_function():
    os.makedirs(TEST_OUTPUT_DIR)
    print("setup")


def teardown_function():
    print("teardown")
    shutil.rmtree(TEST_BASE_OUTPUT_DIR)


def test__get_allocation_url():
    room = "HPH G 1"
    assert (
        _get_allocation_url(room, date(2019, 1, 1).isoformat(), date(2019, 1, 2).isoformat()) ==
        "https://ethz.ch/bin/ethz/roominfo?path=/rooms" +
        "/HPH%20G%201/allocations&from=2019-01-01&to=2019-01-02"
    )


def test__get_filepath():
    assert Path(_get_filepath(room="HPH G 1", output_dir="data/room_allocations")) == \
        Path("data/room_allocations/HPH-G-1.json")


def test_download_json():
    download_json(
        url="https://jsonplaceholder.typicode.com/todos/1",
        filepath=TEST_OUTPUT_FILEPATH,
        metadata=dict(
            room=TEST_ROOM,
            from_date=date(2023, 5, 5).isoformat(),
            to_date=date(2023, 5, 6).isoformat()
        )
    )
    assert open(TEST_OUTPUT_FILEPATH, "r").read() != "", "Downloaded json file is empty."


def test_download_room_allocation():
    download_room_allocation(
        room=TEST_ROOM,
        from_date=date(2023, 5, 5).isoformat(),
        to_date=date(2023, 5, 6).isoformat(),
        output_dir=TEST_OUTPUT_DIR
    )
    assert os.path.exists(TEST_ROOM_FILEPATH), "Downloaded json file does not exist."


def test_get_file_metadata():
    # download test room
    download_room_allocation(
        room=TEST_ROOM,
        from_date=date(2023, 5, 5).isoformat(),
        to_date=date(2023, 5, 6).isoformat(),
        output_dir=TEST_OUTPUT_DIR
    )

    metadata = load_file_metadata(TEST_ROOM_FILEPATH)
    assert metadata["room"] == TEST_ROOM
    assert metadata["from_date"] == date(2023, 5, 5).isoformat()
    assert metadata["to_date"] == date(2023, 5, 6).isoformat()


def test_download_global_room_info():
    download_global_room_info(output_dir=TEST_OUTPUT_DIR)
    assert os.path.exists(TEST_OUTPUT_FILEPATH), "Downloaded json file does not exist."


def test_load_room_allocation():
    # download test room
    download_room_allocation(
        room=TEST_ROOM,
        from_date=date(2023, 5, 5).isoformat(),
        to_date=date(2023, 5, 6).isoformat(),
        output_dir=TEST_OUTPUT_DIR
    )

    allocation = load_room_allocation(TEST_ROOM_FILEPATH)
    assert allocation["room_allocation"], "This should contain the room allocation."
    assert allocation["room_allocation"][0]["date_from"], "This should contain the datetime of 1 allocation."
    assert allocation["room_allocation"][0]["date_to"], "This should contain the datetime of 1 allocation."


def test_load_room_allocations():
    # download test room
    download_room_allocation(
        room=TEST_ROOM,
        from_date=date(2023, 5, 5).isoformat(),
        to_date=date(2023, 5, 6).isoformat(),
        output_dir=TEST_OUTPUT_DIR
    )

    allocations = load_room_allocations(TEST_OUTPUT_DIR)
    assert allocations[0], "This should contain the room allocation of first room."
    assert allocations[0]["room_allocation"][0]["date_from"], \
        "This should contain the datetime of first allocation of first room."
    assert allocations[0]["room_allocation"][0]["date_to"], \
        "This should contain the datetime of first allocation of first room."
