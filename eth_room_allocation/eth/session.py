"""Session to access eth endpoints that require authentication."""

import requests

__session = None


def get_session():
    """Return the session object."""
    global __session
    if __session is None:
        __session = requests.Session()
        __session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
    return __session
