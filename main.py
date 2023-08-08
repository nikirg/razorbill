from pydantic import BaseModel, Field
from fastapi import FastAPI
from typing import Any
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from datetime import  datetime
from razorbill.crud.base import CRUD
from razorbill.router import Router
from razorbill.connectors.memory import MemoryConnector
import asyncio

app = FastAPI()


class UserSchema(BaseModel):
    id: int
    telegram_id: str
    telegram_username: str


class CreateUserSchema(BaseModel):

    telegram_id: str
    telegram_username: str




#def build_api

async def main():
    connector = MemoryConnector(schema=UserSchema)
    crud = CRUD(
        schema =UserSchema,
        create_schema=CreateUserSchema,
        overwrite_create_schema=True,
        connector=connector)

    @crud.after_create
    async def after_create_handler(object: dict[str, Any]) -> dict[str, Any]:
        print("2423")
        print(object)
        return object

    new_user = CreateUserSchema(
        telegram_id="1234",
        telegram_username="asdfasdf"
    )
    item = await crud.create(new_user)
    print(item)

if __name__ == "__main__":
    asyncio.run(main())

    # router = Router(crud=crud)
    # app.include_router()