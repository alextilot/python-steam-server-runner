def make_steamcmd_schema(app_id: str | int):
    """
    Generate a JSON schema for SteamCMD API responses for a given app_id.
    """
    app_id_str = str(app_id)
    return {
        "type": "object",
        "required": ["data"],
        "properties": {
            "data": {
                "type": "object",
                "required": [app_id_str],
                "properties": {
                    app_id_str: {
                        "type": "object",
                        "required": ["depots"],
                        "properties": {
                            "depots": {
                                "type": "object",
                                "required": ["branches"],
                                "properties": {
                                    "branches": {
                                        "type": "object",
                                        "required": ["public"],
                                        "properties": {
                                            "public": {
                                                "type": "object",
                                                "required": ["buildid"],
                                                "properties": {
                                                    "buildid": {"type": "string"}
                                                },
                                            }
                                        },
                                    }
                                },
                            },
                        },
                    }
                },
            }
        },
    }
