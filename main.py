import os
from fastapi import FastAPI
from sqlalchemy import create_engine, text

app = FastAPI()

# ===============================
# DATABASE CONFIG (Render + psycopg v3)
# ===============================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

# Force psycopg v3
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# ===============================
# TEST ROUTE
# ===============================

@app.get("/")
def home():
    return {"status": "JobChap is running 🚀"}

# ===============================
# DB TEST
# ===============================

@app.get("/db-test")
def db_test():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return {"db": result.scalar()}