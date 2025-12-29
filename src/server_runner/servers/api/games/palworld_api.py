from typing import Any

from requests.auth import HTTPBasicAuth
from rest_api_base import RESTSteamGameAPI


class PalWorldAPI(RESTSteamGameAPI):
    """
    Palworld REST API client using the reusable RESTSteamGameAPI base.
    """

    def __init__(
        self, base_url: str, username: str, password: str, timeout: int = 10
    ) -> None:
        auth = HTTPBasicAuth(username, password)
        super().__init__(base_url=base_url, auth=auth, timeout=timeout)

    # ------------------------
    # Server Info
    # ------------------------
    def info(self) -> dict[str, Any]:
        """Get server information."""
        return self._get("/v1/api/info")

    def players(self) -> list[dict[str, Any]]:
        """Get player list."""
        return self._get("/v1/api/players").get("players", [])

    def settings(self) -> dict[str, Any]:
        """Get server settings."""
        return self._get("/v1/api/settings")

    def metrics(self) -> dict[str, Any]:
        """Get server metrics."""
        return self._get("/v1/api/metrics")

    # ------------------------
    # Server Control
    # ------------------------
    def announce(self, message: str) -> None:
        """Send a server-wide announcement."""
        self._post("/v1/api/announce", {"message": message})

    def save(self) -> None:
        """Save the server state."""
        self._post("/v1/api/save", {})

    def shutdown(self, message: str, delay: int = 10) -> None:
        """Shutdown the server with optional message and delay."""
        self._post("/v1/api/shutdown", {"waittime": delay, "message": message})

    def stop(self) -> None:
        """Stop the server immediately."""
        self._post("/v1/api/stop", {})
