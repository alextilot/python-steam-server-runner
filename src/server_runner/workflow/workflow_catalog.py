from typing import Generic, TypeVar

from config.logging import get_logger

log = get_logger()

K = TypeVar("K")
V = TypeVar("V")


class WorkflowCatalog(Generic[K, V]):
    """
    A registry mapping workflow identifiers to factory functions or handlers.
    Useful for looking up workflow types, builders, or actions.
    """

    def __init__(self) -> None:
        self._registry: dict[K, V] = {}

    def register(self, key: K, value: V) -> None:
        if key in self._registry:
            msg = f"WorkflowRegistry: duplicate registration for key '{key}'"
            log.error(msg)
            raise KeyError(msg)
        self._registry[key] = value

    def get(self, key: K) -> V | None:
        return self._registry.get(key)

    def __contains__(self, key: K) -> bool:
        return key in self._registry

    def keys(self):
        return self._registry.keys()
