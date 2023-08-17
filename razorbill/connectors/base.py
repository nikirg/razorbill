from abc import ABC, abstractmethod
from typing import Any, Type
from pydantic import BaseModel


class BaseConnector(ABC):
    @property
    @abstractmethod
    def schema(self) -> Type[BaseModel]:
        pass

    @property
    @abstractmethod
    def pk_name(self) -> str:
        pass

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        pass

    @abstractmethod
    async def get_many(
            self, skip: int, limit: int, filters: dict[str, Any] | None = None
    ) -> list[BaseModel]:
        pass

    @abstractmethod
    async def get_one(self, obj_id: str | int) -> BaseModel:
        pass

    @abstractmethod
    async def create_one(self, obj: BaseModel) -> BaseModel:
        pass

    @abstractmethod
    async def update_one(
            self, obj_id: str | int, obj: BaseModel
    ) -> BaseModel:
        pass

    @abstractmethod
    async def delete_one(self, obj_id: str | int) -> bool:
        pass
