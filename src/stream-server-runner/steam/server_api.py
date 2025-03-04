import logging

import requests

log = logging.getLogger(__name__)


class ServerAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def call(self, method_name: str, *args, **kwargs):
        method = getattr(self, method_name, None)
        if callable(method):
            return method(*args, **kwargs)
        else:
            log.error("Method not found")

    def request(self, method: str, endpoint: str, headers: dict, data: str | dict):
        url = f"{self.base_url}/{endpoint}"
        try:
            log.debug(
                f"Request to: method={method}, endpoint={url} header={headers} data={data}"
            )
            response = requests.request(method, url, headers=headers, data=data)
            response.raise_for_status()
            log.debug(f"Request response: {response}, {response.text}")
            return response.text
        except Exception as e:
            log.error(f"Request failed: {e}")
            return None
