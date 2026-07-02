from typing import Annotated

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

int_pk = Annotated[int, mapped_column(Integer, primary_key=True)]


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(self) -> str:
        return self.__name__.lower()


class RawJob(Base):
    __tablename__ = "jobs_raw"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    job_title = Column(String(255), nullable=False)
    job_link = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    published_date = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<RawJob(platform='{self.platform}', title='{self.job_title}')>"


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    Title = Column(String(255), nullable=False)
    Link = Column(String, nullable=True)
    Skills = Column(Text, nullable=True)
    Price = Column(String(50), nullable=True)
    Description = Column(Text, nullable=True)
    platform_source = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<TrainingJob(title='{self.Title}')>"


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"
    id: Mapped[int_pk]
