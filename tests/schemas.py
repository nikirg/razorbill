from pydantic import BaseModel

class ProjectSchema(BaseModel):
    id: int
    name: str


class CreateProjectSchema(BaseModel):
    name: str


class UserSchema(BaseModel):
    id: int
    telegram_id: str
    telegram_username: str
    project_id: int | None = None


class CreateUserSchema(BaseModel):
    telegram_id: str
    telegram_username: str
    project_id: int | None = None
