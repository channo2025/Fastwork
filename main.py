import os
from datetime import datetime

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import create_engine, text

# ===============================
# APP
# ===============================
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ===============================
# DATABASE (PostgreSQL - Render)
# ===============================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

# Fix Render postgres:// -> psycopg v3
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
# CREATE TABLE (SAFE)
# ===============================
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            city TEXT NOT NULL,
            pay TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    """))

# ===============================
# ROUTES
# ===============================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    with engine.connect() as conn:
        jobs = conn.execute(
            text("SELECT * FROM jobs ORDER BY created_at DESC")
        ).mappings().all()

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "jobs": jobs}
    )


@app.get("/post-job", response_class=HTMLResponse)
def post_job_page(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {"request": request}
    )


@app.post("/post-job")
def post_job(
    title: str = Form(...),
    category: str = Form(...),
    city: str = Form(...),
    pay: str = Form(...),
    description: str = Form(...)
):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO jobs (title, category, city, pay, description, created_at)
                VALUES (:title, :category, :city, :pay, :description, :created_at)
            """),
            {
                "title": title,
                "category": category,
                "city": city,
                "pay": pay,
                "description": description,
                "created_at": datetime.utcnow()
            }
        )

    return RedirectResponse("/", status_code=303)