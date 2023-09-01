# flake8: noqa: C0116,W0611

def setup_function():
    print("setup")


def teardown_function():
    print("teardown")


def test_dummy():
    assert True, ""
