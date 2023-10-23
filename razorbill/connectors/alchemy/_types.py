from typing import TypeVar

from sqlalchemy.orm import DeclarativeBase

AlchemyModel = TypeVar("AlchemyModel", bound=DeclarativeBase)