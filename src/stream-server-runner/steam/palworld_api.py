import json
import logging
from base64 import b64encode
from enum import StrEnum

from steam.server_api import ServerAPI

log = logging.getLogger(__name__)


def args_to_string(*args):
    string = ""
    for arg in args:
        string += str(arg) + " "
    return string.strip()


def string_to_args_kwargs(input_string: str):
    args = []
    kwargs = {}
    parts = input_string.split()
    i = 0
    while i < len(parts):
        if "=" in parts[i]:
            key, value = parts[i].split("=", 1)
            kwargs[key] = value
        else:
            args.append(parts[i])
        i += 1
    return args, kwargs


def join_args_kwargs(*args, **kwargs):
    """Joins all positional and keyword arguments into a single string."""
    arg_strings = [str(arg) for arg in args]
    kwarg_strings = [f"{key}={value}" for key, value in kwargs.items()]
    combined_string = " ".join(arg_strings + kwarg_strings)
    if len(combined_string) == 0:
        return ""
    return f" {combined_string}"


def basic_auth(username: str, password: str):
    token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


class PalworldiAPIEndpoints(StrEnum):
    ANNOUNCE = "announce"
    SAVE = "save"
    SHUTDOWN = "shutdown"
    STOP = "stop"


class PalWorldAPI(ServerAPI):
    def __init__(self, base_url: str, username: str, password: str):
        super().__init__(base_url)
        self.auth = basic_auth(username, password)

    def call(self, method_name: str, *args):
        try:
            method = getattr(self, method_name, None)
            input = args_to_string(*args)
            if callable(method):
                str_args, str_kwargs = string_to_args_kwargs(input)
                return method(*str_args, **str_kwargs)
            else:
                return self.announce(method_name, *args)
        except Exception as e:
            log.error(f"Error on calling {method_name}: {e}")

    def info(self):
        headers = {
            "Authorization": self.auth,
            "Content-Type": "application/json",
        }
        payload = {}
        return self.request("GET", "info", headers, payload)

    def players(self):
        headers = {
            "Authorization": self.auth,
            "Content-Type": "application/json",
        }
        payload = {}
        return self.request("GET", "players", headers, payload)

    def settings(self):
        headers = {
            "Authorization": self.auth,
            "Content-Type": "application/json",
        }
        payload = {}
        return self.request("GET", "settings", headers, payload)

    def metrics(self):
        headers = {
            "Authorization": self.auth,
            "Content-Type": "application/json",
        }
        payload = {}
        return self.request("GET", "metrics", headers, payload)

    def announce(self, *args):
        headers = {
            "Authorization": self.auth,
            "Content-Type": "application/json",
        }
        message = args_to_string(*args)
        payload = json.dumps(
            {
                "message": message,
            }
        )
        return self.request("POST", "announce", headers, payload)

    def save(self):
        headers = {
            "Authorization": self.auth,
        }
        payload = {}
        return self.request("POST", "save", headers, payload)

    def shutdown(self, *args, delay=10):
        headers = {
            "Authorization": self.auth,
            "Content-Type": "application/json",
        }
        message = args_to_string(*args)
        payload = json.dumps({"waittime": delay, "message": message})
        return self.request("POST", "shutdown", headers, payload)

    def stop(self):
        headers = {
            "Authorization": self.auth,
        }
        payload = {}
        return self.request("POST", "stop", headers, payload)
