from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)

class User(Base):
    __tablename__ = "users"
    
    name: Mapped[str] = mapped_column()
    blog: Mapped["Blog"] = relationship(back_populates="user")


class Blog(Base):
    __tablename__ = "blogs"
    
    title: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="blog")


