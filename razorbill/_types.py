from typing import Dict, TypeVar, Optional, Sequence
from fastapi.params import Depends
from pydantic import BaseModel
T = TypeVar("T", bound=BaseModel)
DEPENDENCIES = Optional[Sequence[Depends]]

