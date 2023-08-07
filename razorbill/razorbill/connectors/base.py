from abc import ABC, abstractmethod
from typing import Any, Type

from .razorbill.model import BaseDataModel


class BaseConnector(ABC):
    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        pass

    @abstractmethod
    async def get_many(
        self, skip: int, limit: int, filters: dict[str, Any] | None = None
    ) -> list[Type[BaseDataModel]]:
        pass

    @abstractmethod
    async def get_one(self, obj_id: str | int) -> Type[BaseDataModel]:
        pass

    @abstractmethod
    async def create_one(self, obj: dict[str, Any]) -> Type[BaseDataModel]:
        pass

    @abstractmethod
    async def update_one(
        self, obj_id: str | int, obj: dict[str, Any]
    ) -> Type[BaseDataModel]:
        pass

    @abstractmethod
    async def delete_one(self, obj_id: str | int):
        pass
