from typing import TypedDict


class PasswordAuth(TypedDict):
    username: str
    password: str


class TokenAuth(TypedDict):
    token: str


AuthInfo = PasswordAuth | TokenAuth
