from abc import ABC
from typing import Any, Type
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, validate_arguments
from pymongo.errors import DuplicateKeyError
import pymongo
from bson import ObjectId
from beanie import PydanticObjectId
from razorbill.connectors.base import BaseConnector
from razorbill.connectors.mongo.utils import _prepare_result, validate_id
from beanie import init_beanie, Document
from functools import wraps
from razorbill.connectors.mongo.utils import create_beanie_model


class AsyncMongoConnectorException(Exception):
    pass


def ensure_initialized(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.initialized:
            await self.init_beanie()
        return await func(self, *args, **kwargs)

    return wrapper


class AsyncMongoConnector(BaseConnector):
    @validate_arguments
    def __init__(self, url: str, model: Type[BaseModel], pk_name: str = "id") -> None:
        self.document_schema = create_beanie_model(model, model.__name__, pk_name)
        self.db_name = url.split('/')[-1]
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(url)
        self._schema = self.document_schema  # update_mongo_schema(model)
        self._pk_name = pk_name
        self.initialized = False

    @property
    def pk_name(self) -> str:
        return self._pk_name

    @property
    def schema(self) -> Type[BaseModel]:
        return self._schema

    async def init_beanie(self):
        await init_beanie(database=self.client[self.db_name], document_models=[self.document_schema])
        self.initialized = True

    @ensure_initialized
    async def count(self, filters: dict[str, Any] = {}) -> int:
        if filters:
            query = self.document_schema.find(filters)
        else:
            query = self.document_schema.find()
        return await query.count()

    @ensure_initialized
    async def create_one(self, obj: dict[str, Any]) -> dict[str, Any]:
        try:
            new_document = self.document_schema(**obj)
            new_obj = await new_document.insert()
            return new_obj

        except DuplicateKeyError:
            raise AsyncMongoConnectorException(f"Duplicate key error")

    @ensure_initialized
    async def get_many(
            self,
            skip: int,
            limit: int,
            filters: dict[str, Any] = {},
            populate: bool = False,
            sorting: dict[str, bool] = None
    ) -> list[dict[str, Any]]:
        query = self.document_schema.find(filters) if filters else self.document_schema.find()
        if sorting:
            sort_fields = [(field if field != 'id' else "_id", pymongo.DESCENDING if sort_desc else pymongo.ASCENDING)
                           for field, sort_desc in sorting.items()]
            query = query.sort(sort_fields)
        query = query.skip(skip).limit(limit)
        return await query.to_list()

    @ensure_initialized
    async def get_one(
            self,
            obj_id: str | int,
            filters: dict[str, Any] = {},
            populate: bool = False
    ) -> dict[str, Any] | None:
        obj_id = validate_id(obj_id)
        if obj_id is None:
            return None
        result = await self.document_schema.get(obj_id)
        if not result:
            return None

        return _prepare_result(result, [])

    @ensure_initialized
    async def update_one(
            self, obj_id: str | int,
            obj: dict[str, Any],
            filters: dict[str, Any] = {}
    ) -> dict[str, Any]:

        document = await self.document_schema.get(obj_id)
        result = await document.update({"$set": obj})

        if not result:
            return None

        return result

    @ensure_initialized
    async def delete_one(self, obj_id: str | int, filters: dict[str, Any] = {}) -> bool:
        document = await self.document_schema.get(obj_id)
        result = await document.delete()

        if not result:
            return None

        return result

#
# class AsyncMongoConnector(BaseConnector):
#     @validate_arguments
#     def __init__(self, url: str, model: Type[BaseModel], pk_name: str = "id") -> None:
#         self.document_schema = create_beanie_model(model, model.__name__, pk_name)
#
#         self.client: AsyncIOMotorClient = AsyncIOMotorClient(url)
#         self.db: AsyncIOMotorDatabase = self.client['razorbill']
#         self.collection = self.db[self.document_schema.__name__.lower()]
#         self._schema = update_mongo_schema(model)
#         self._pk_name = pk_name
#
#
#     @property
#     def pk_name(self) -> str:
#         return self._pk_name
#
#     @property
#     def schema(self) -> Type[BaseModel]:
#         return self._schema
#
#     # async def init_beanie(self):
#     #     await init_beanie(database=self.client.db_name, document_schemas=[self.document_schema])
#
#     async def create_one(self, obj: dict[str, Any]) -> dict[str, Any]:
#         try:
#             result = await self.collection.insert_one(obj)
#             obj['_id'] = result.inserted_id
#             return obj
#
#         except DuplicateKeyError:
#             raise AsyncMongoConnectorException(f"Duplicate key error")
#
#     async def count(self, filters: dict[str, Any] = {}) -> int:
#
#         return await self.collection.count_documents(filters if filters else {})
#
#     async def get_many(
#             self,
#             skip: int,
#             limit: int,
#             filters: dict[str, Any] = {},
#             populate: bool = False,
#             sorting: dict[str, bool] = None
#     ) -> list[dict[str, Any]]:
#         cursor = self.collection.find(filters).skip(skip).limit(limit)
#
#         if sorting:
#             sort = [(field, pymongo.DESCENDING if sort_desc else pymongo.ASCENDING) for field, sort_desc in
#                     sorting.items()]
#             cursor = cursor.sort(sort)
#
#         results = await cursor.to_list(length=limit)
#         print(results)
#         return results
#         #return [_prepare_result(result) for result in results]
#
#     async def get_one(
#             self,
#             obj_id: str | int,
#             filters: dict[str, Any] = {},
#             populate: bool = False
#     ) -> dict[str, Any] | None:
#         query = {'_id': obj_id}
#         result = await self.collection.find_one(query, filters)
#         print(result)
#         if not result:
#             return None
#
#         return _prepare_result(result, [])
#
#     async def update_one(
#             self, obj_id: str | int,
#             obj: dict[str, Any],
#             filters: dict[str, Any] = {}
#     ) -> dict[str, Any]:
#         query = {'_id': obj_id}
#         update = {'$set': obj}
#
#         result = await self.collection.find_one_and_update(query, update, return_document=pymongo.ReturnDocument.AFTER)
#
#         if not result:
#             return None
#
#         return _prepare_result(result)
#
#     async def delete_one(self, obj_id: str | int, filters: dict[str, Any] = {}) -> bool:
#         query = {'_id': obj_id}
#         result = await self.collection.delete_one(query)
#         return result.deleted_count > 0
