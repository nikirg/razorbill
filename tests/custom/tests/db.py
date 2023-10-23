import os
import asyncio
from loguru import logger

from fastapi import FastAPI

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from razorbill.connectors.alchemy.tests.models import Base, Blog, User
from razorbill.connectors.alchemy.connector import AsyncSQLAlchemyConnector
from razorbill.crud import CRUD
from razorbill.router import Router

DB_FILE_PATH = os.path.join(os.path.dirname(__file__), "test.db")
DB_URL = f"sqlite+aiosqlite:///file:{DB_FILE_PATH}?mode=memory&cache=shared&uri=true"


async def init_db() -> sessionmaker:
    engine: AsyncEngine = create_async_engine(url=DB_URL, echo=False)
    session_maker: sessionmaker = sessionmaker(engine, class_=AsyncSession) # type: ignore
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    return session_maker
    
app = FastAPI()
# async def test():

@app.on_event("startup")
async def init():
    session_maker = await init_db()

    user_connector = AsyncSQLAlchemyConnector(User, session_maker=session_maker)
    user_crud = CRUD(user_connector)
    user_router = Router(user_crud)
    
    model_connector = AsyncSQLAlchemyConnector(Blog, session_maker=session_maker)
    model_crud = CRUD(model_connector)
    model_router = Router(model_crud, parent_crud=user_crud)
    
    app.include_router(user_router)
    app.include_router(model_router)
    
    
    # user_obj = await user_connector.create_one({"name": "Тест"})
    # logger.debug(user_obj)
    
    # count = await user_connector.count()
    # logger.debug(count)
    
    # model_obj = await model_connector.create_one({
    #     "title": "Блог про Тест", 
    #     "user_id": user_obj["id"]
    # })
    # logger.debug(model_obj)
    
    # count = await model_connector.count()
    # logger.debug(count)
    
    # model_obj = await model_connector.update_one(model_obj["id"], {
    #     "title": "БАЗА УПАЛА", 
    #     "user_id": user_obj["id"]
    # })
    # logger.debug(model_obj)
    

    # model_obj = await model_connector.get_one(model_obj["id"])
    # logger.debug(model_obj)
    
    # items = await model_connector.get_many(0, 10, populate=["User"])
    # logger.debug(items)
    
    

    # model_obj = await model_connector.delete_one(model_obj["id"])
    
    # count = await model_connector.count()
    # logger.debug(count)
    
    
    
# if __name__ == "__main__":  
#     asyncio.run(test())