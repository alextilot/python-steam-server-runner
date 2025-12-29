from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any, TypeVar

import requests
from requests.auth import AuthBase

T = TypeVar("T")

ParamsKey = str | bytes | int | float
ParamsValue = str | bytes | int | float | Iterable[str | bytes | int | float] | None
RequestParams = Mapping[ParamsKey, ParamsValue]

JsonMapping = Mapping[str, object]


class RESTSteamGameAPI(ABC):
    """
    Base class for RESTful Steam game APIs.
    Handles GET/POST requests and defines abstract server methods.
    """

    def __init__(self, base_url: str, auth: AuthBase | None = None, timeout: int = 10):
        """
        Args:
            base_url: Base URL of the REST API (e.g., "http://localhost:8212").
            auth: Optional requests-compatible authentication (e.g., HTTPBasicAuth).
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.timeout = timeout

    # ------------------------
    # HTTP Helpers
    # ------------------------
    def _get(
        self, endpoint: str, params: RequestParams | None = None
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(
                url, auth=self.auth, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.RequestException as e:
            raise RuntimeError(f"GET {url} failed: {e}") from e

    def _post(self, endpoint: str, json: JsonMapping | None = None) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.post(
                url, auth=self.auth, json=json, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.RequestException as e:
            raise RuntimeError(f"POST {url} failed: {e}") from e

    # ------------------------
    # Abstract Server Methods
    # ------------------------
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
