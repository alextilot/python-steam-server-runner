from typing import Any

from requests.auth import HTTPBasicAuth

from server_runner.steam.api.auth_info import AuthInfo
from server_runner.steam.api.rest_api_base import RESTSteamServerAPI


class PalWorldAPI(RESTSteamServerAPI):
    """
    Palworld REST API client using the reusable RESTSteamServerAPI base.
    """

    def _build_auth(self, auth_info: AuthInfo | None):
        if not auth_info:
            raise ValueError("auth_info is required")

        username = auth_info.get("username")
        password = auth_info.get("password")

        if not isinstance(username, str) or not username:
            raise ValueError("auth_info.username must be a non-empty string")

        if not isinstance(password, str) or not password:
            raise ValueError("auth_info.password must be a non-empty string")

        return HTTPBasicAuth(username, password)

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
