import os
from fastapi import FastAPI
from sqlalchemy import create_engine, text

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

# ✅ Force psycopg v3 (Render peut donner postgres:// ou postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

@app.get("/")
def home():
    return {"status": "JobChap is running 🚀"}

@app.get("/db-test")
def db_test():
    with engine.connect() as conn:
        return {"db": conn.execute(text("SELECT 1")).scalar()}