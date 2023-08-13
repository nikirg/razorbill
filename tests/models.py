from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, nullable=False)
    telegram_username = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship("Project", back_populates="users")


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    users = relationship("User", back_populates="project")
