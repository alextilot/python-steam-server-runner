from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any, TypeVar

import requests

from server_runner.steam.api.auth_info import AuthInfo

T = TypeVar("T")

ParamsKey = str | bytes | int | float
ParamsValue = str | bytes | int | float | Iterable[str | bytes | int | float] | None
RequestParams = Mapping[ParamsKey, ParamsValue]

JsonMapping = Mapping[str, object]


class SteamAPIRequestError(RuntimeError):
    """Raised when a REST request to a Steam server fails."""


class RESTSteamServerAPI(ABC):
    """
    Base class for RESTful Steam game APIs.
    Handles GET/POST requests and defines abstract server methods.
    """

    def __init__(
        self, *, base_url: str, auth_info: AuthInfo | None = None, timeout: int = 10
    ):
        """
        Args:
            base_url: Base URL of the REST API (e.g., "http://localhost:8212").
            auth_info: Optional requests-compatible authentication (e.g., HTTPBasicAuth).
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.auth = self._build_auth(auth_info)
        self.timeout = timeout

    # ------------------------
    # HTTP Helpers
    # ------------------------
    def _full_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _get(
        self, endpoint: str, params: RequestParams | None = None
    ) -> dict[str, Any]:
        url = self._full_url(endpoint)
        try:
            response = requests.get(
                url, auth=self.auth, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.RequestException as e:
            raise SteamAPIRequestError(f"GET {url} failed: {e}") from e

    def _post(
        self, endpoint: str, json: JsonMapping | None = None
    ) -> dict[str, Any] | None:
        url = self._full_url(endpoint)
        try:
            response = requests.post(
                url, auth=self.auth, json=json, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.RequestException as e:
            raise SteamAPIRequestError(f"POST {url} failed: {e}") from e

    # ------------------------
    # Abstract Server Methods
    # ------------------------
    @abstractmethod
    def _build_auth(self, auth_info: AuthInfo | None) -> Any:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Get server info (health check)"""
        pass

    @abstractmethod
    def announce(self, message: str) -> None:
        """Send an announcement message to the server."""
        pass

    @abstractmethod
    def save(self) -> None:
        """Trigger a server save."""
        pass

    @abstractmethod
    def shutdown(self, message: str, delay: int) -> None:
        """Shutdown the server with a message after a delay (in seconds)."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the server via the API."""
        pass
