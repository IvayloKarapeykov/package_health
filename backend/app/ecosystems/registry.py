from collections.abc import Iterable

from app.domain.errors import InvalidInputError
from app.domain.models import Ecosystem
from app.ecosystems.base import EcosystemAdapter


class EcosystemRegistry:
    def __init__(self, adapters: Iterable[EcosystemAdapter]) -> None:
        self._adapters = {adapter.id: adapter for adapter in adapters}

    def get(self, ecosystem: Ecosystem) -> EcosystemAdapter:
        try:
            return self._adapters[ecosystem]
        except KeyError:
            raise InvalidInputError(f"Unsupported ecosystem '{ecosystem}'.") from None

    def all(self) -> list[EcosystemAdapter]:
        return list(self._adapters.values())
