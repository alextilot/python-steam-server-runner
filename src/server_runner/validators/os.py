import os


def os_path_exists_raise(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError
