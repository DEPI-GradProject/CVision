from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


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
