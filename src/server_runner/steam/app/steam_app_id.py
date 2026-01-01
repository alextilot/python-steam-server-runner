from enum import IntEnum


class SteamAppID(IntEnum):
    PALWORLD_DEDICATED_SERVER = 2394010
    # VALHEIM = 896660
    # SATISFACTORY = 1690800


def get_steam_app_id(app_id: int) -> SteamAppID:
    try:
        return SteamAppID(app_id)
    except ValueError as e:
        raise ValueError(f"Unsupported Steam server App ID: {app_id}") from e
