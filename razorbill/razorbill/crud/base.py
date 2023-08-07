from typing import Any, Type, Callable
from abc import ABC, abstractmethod
import dataclasses
from enum import Enum

from pydantic import BaseModel, validate_arguments

from razorbill.connectors.base import BaseConnector

class BaseCRUD(ABC):
    @abstractmethod
    def __init__(
        self, 
        data_model: Any, 
        connector: Type[BaseConnector] = InmemoryConnector(),
        schema: Type[BaseModel] | None = None,
        create_schema: Type[BaseModel] | None = None,
        update_schema: Type[BaseModel] | None = None,
        overwrite_schema: bool = False,
        overwrite_create_schema: bool = False,
        overwrite_update_schema: bool = False
    ):
        self.data_model = data_model
        self._connector = connector
        
        async def dummy(arg: Type[BaseModel] | Type[BaseDataModel] | str | int): return arg

        self._before_create_func = dummy
        self._before_update_func = dummy
        self._before_delete_func = dummy
        
        self._after_create_func = dummy
        self._after_update_func = dummy
        self._after_delete_func = dummy
    
    @abstractmethod
    @validate_arguments
    def before_create(self, func: Callable) -> Callable:
        self._before_create_func = func
        return func
    
    @abstractmethod
    @validate_arguments
    def before_update(self, func: Callable) -> Callable:
        self._before_update_func = func
        return func
    
    @abstractmethod
    @validate_arguments
    def before_delete(self, func: Callable) -> Callable:
        self._before_delete_func = func
        return func     
    
    @abstractmethod   
    @validate_arguments
    def after_create(self, func: Callable) -> Callable:
        self._after_update_func = func
        return func
    
    @abstractmethod
    @validate_arguments
    def after_update(self, func: Callable) -> Callable:
        self._before_create_func = func
        return func
    
    @abstractmethod
    @validate_arguments
    def after_delete(self, func: Callable) -> Callable:
        self._after_delete_func = func
        return func
    
    @abstractmethod
    async def get_one(self, item_id: str | int):
        item: BaseModel = await self._connector.get_one(item_id)
    
    @abstractmethod
    async def get_many(self, skip: int, limit: int, filters: dict[str, Any] = {}, sorting: dict[str, tuple[Any, str]] = {}):
        return await self._connector.get_many(skip, limit, filters=filters, sorting=sorting)
    
    @abstractmethod
    async def create(self, item: Type[BaseModel]):
        item = await self._before_create_func(item)
        record = await self._connector.create_one(item)
        record = await self._after_create_func(record)
        # TODO проверить, не делает ли повторную валидацию fastapi в роутере
        return self.schema(**record)
    
    @abstractmethod
    async def update(self, item_id: str | int, item: Type[BaseModel]):
        _item = await self._before_update_func(item_id, item)
        record = await self._connector.update_one(item_id, _item)
        return await self._after_update_func(record)
    
    @abstractmethod
    async def delete(self, item_id: str | int) -> Type[BaseDataModel]:
        await self._before_delete_func(item_id)
        record = await self._connector.delete_one(item_id)
        return await self._after_delete_func(record)
    
    
if __name__ == "main":
    data_model = ""
    connector = ""
    crud = CRUD(data_model, connector)
    
    @crud.before_create
    def before_create_handler(object: BaseModel) -> BaseModel:
        return crud.Schema(**object.dict(), status="on")
    
    @crud.after_create
    def after_create_handler(item_id: int | str, object: dict[str, Any]) -> dict[str, Any]:
        return {}
    
    @crud.before_update
    def before_update_handler(item_id: int | str, object: BaseModel) -> BaseModel:
        return crud.Schema(**object.dict(), updated=True)
    
    @crud.after_update
    def after_update_handler(item_id: int | str, object: dict[str, Any]) -> dict[str, Any]:
        return {}
    
    @crud.before_delete
    def before_delete_handler(item_id: int | str):
        project = crud.get_one(item_id)
        
        for user_id in project.users:
            pass
    
    @crud.after_delete
    def after_delete_handler(item_id: int | str):
        pass
            
        