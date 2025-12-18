import os
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ======================
# DATABASE CONFIG
# ======================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fastwork_db.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ======================
# MODELS
# ======================

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)


# ======================
# CREATE TABLES
# ======================

Base.metadata.create_all(bind=engine)


# ======================
# FASTAPI APP
# ======================

app = FastAPI(title="JobDash API")


# ======================
# DEPENDENCIES
# ======================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ======================
# ROUTES
# ======================

@app.get("/")
def root():
    return {"status": "JobDash API is running 🚀"}


@app.post("/jobs")
def create_job(title: str, description: str = "", db: Session = Depends(get_db)):
    job = Job(title=title, description=description)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()