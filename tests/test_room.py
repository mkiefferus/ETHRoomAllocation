# flake8: noqa: C0116,W0611


def setup_function():
    print("setup")


def teardown_function():
    print("teardown")


def test_room_update():
    """TODO: Test if the room updates if the allocation is not up to date"""
    assert True, ""


def test_room_get_slots():
    """TODO: Test if the room returns the correct slots corresponding to the given datetimes"""
    assert True, ""


def test_room_get_available_slots():
    """TODO: Test if the room returns the correct available (7,15) slots corresponding to the given
    datetimes"""
    assert True, ""


def test_room_is_available():
    """TODO: Test if the room returns the correct availability corresponding to the given datetimes"""
    assert True, ""
