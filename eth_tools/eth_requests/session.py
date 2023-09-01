# flake8: noqa: PLW613, PLC115

"""Session to access eth endpoints that require authentication."""

from requests import Session


class ETHSession(Session):
    def __init__(self) -> None:
        super().__init__()
        self.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "*/*"})


class ETHSessionWithAuth(ETHSession):
    def __init__(self, username: str, password: str) -> None:
        super().__init__()
        raise NotImplementedError("TODO: implement auth")
