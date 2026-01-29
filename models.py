from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    city = Column(Text, nullable=False)
    pay = Column(Text, nullable=True)
    description = Column(Text, nullable=False)

    # ✅ infos employeur / poster
    poster_email = Column(String(160), nullable=False)
    poster_phone = Column(String(80), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)

    # ✅ infos candidat
    applicant_name = Column(String(120), nullable=False)
    applicant_email = Column(String(160), nullable=False)
    applicant_phone = Column(String(80), nullable=True)
    message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job = relationship("Job", back_populates="applications")