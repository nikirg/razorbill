from typing import Any, Type

from sqlalchemy.orm import DeclarativeBase


def object_to_dict(obj: Type[DeclarativeBase]) -> dict[str, Any]:
    return {c.name: str(getattr(obj, c.name)) for c in obj.__table__.columns}