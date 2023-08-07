from abc import ABC, abstractmethod

from sqlalchemy.orm import DeclarativeBase as SQLAlchemyBaseModel

class BaseDataModel(ABC):
    @abstractmethod
    def to_dict(self) -> dict:
        pass


class AlchemyModel(SQLAlchemyBaseModel, BaseDataModel):
    def to_dict(self) -> dict:
        return self.__dict__

#class BeanieModel(BaseDataModel, BeanieDocument):
#    pass

#class RedisModel(BaseDataModel, RedisHashModel):
#    pass

class CRUD:
    pass

class Article(SQLAlchemyBaseModel):
    title: str
    description: str
    created_at: int

article_crud = CRUD(Article)


@article_crud.after_delete
def func()
    
    
