import asyncio
import pytest
from crud import CRUD
from tests.models import User, Project


def new_project(name):
    return Project(
        name=name,
    )


def new_user(telegram_id: str, telegram_username: str, project_id: int = None):
    return User(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        project_id=project_id
    )


@pytest.mark.asyncio
async def test_get_many_without_filters(user_alchemy_connector, project_alchemy_connector):
    await user_alchemy_connector.drop_all_tables()
    await project_alchemy_connector.drop_all_tables()
    user_crud = CRUD(
        schema=user_alchemy_connector.schema,
        connector=user_alchemy_connector)
    project_crud = CRUD(
        schema=project_alchemy_connector.schema,
        connector=project_alchemy_connector)
    project = await project_crud.create(new_project("Test Project"))
    await user_crud.create(new_user("1", "test1", project.id))
    await user_crud.create(new_user("2", "test2", project.id))
    await user_crud.create(new_user("3", "test3"))
    users = await user_crud.get_many(skip=0, limit=10)
    print(f"in get_many without filter {users}")
    assert len(users) == 3


@pytest.mark.asyncio
async def test_get_many_with_filters(user_alchemy_connector, project_alchemy_connector):
    await user_alchemy_connector.drop_all_tables()
    await project_alchemy_connector.drop_all_tables()
    user_crud = CRUD(
        schema=user_alchemy_connector.schema,
        connector=user_alchemy_connector)
    project_crud = CRUD(
        schema=project_alchemy_connector.schema,
        connector=project_alchemy_connector)
    project = await project_crud.create(new_project("Test Project"))
    await user_crud.create(new_user("1", "test1", project.id))
    await user_crud.create(new_user("2", "test2", project.id))
    await user_crud.create(new_user("3", "test3"))
    filter = {"project_id": project.id}
    users = await user_crud.get_many(skip=0, limit=10, filters=filter)
    print(f"in get_many with filter {users}")
    assert len(users) == 2
