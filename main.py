from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from datetime import datetime
import os

# =========================================================
# APP
# =========================================================
app = FastAPI()

templates = Jinja2Templates(directory="templates")

# =========================================================
# DATABASE (PostgreSQL on Render)
# =========================================================
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL not set")

engine = create_engine(DATABASE_URL)

# =========================================================
# CREATE TABLES (PostgreSQL compatible)
# =========================================================
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
        );
    """))

# =========================================================
# ROUTES
# =========================================================

# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    with engine.connect() as conn:
        jobs = conn.execute(
            text("SELECT * FROM jobs ORDER BY created_at DESC")
        ).fetchall()

    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "jobs": jobs
        }
    )

# ---------------- POST JOB (PAGE) ----------------
@app.get("/post-job", response_class=HTMLResponse)
def post_job_page(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})

# ---------------- POST JOB (FORM) ----------------
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

    return RedirectResponse("/thank-you?m=job_posted", status_code=303)

# ---------------- JOB DETAILS ----------------
@app.get("/job/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    with engine.connect() as conn:
        job = conn.execute(
            text("SELECT * FROM jobs WHERE id = :id"),
            {"id": job_id}
        ).fetchone()

    if not job:
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "jobs": [job]
        }
    )

# ---------------- APPLY ----------------
@app.post("/apply")
def apply_job():
    return RedirectResponse("/apply-success", status_code=303)

# ---------------- APPLY SUCCESS ----------------
@app.get("/apply-success", response_class=HTMLResponse)
def apply_success(request: Request):
    return templates.TemplateResponse(
        "thank_you.html",
        {
            "request": request,
            "message": "Application sent successfully!"
        }
    )

# ---------------- THANK YOU ----------------
@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request, m: str = ""):
    msg = "Success!"
    if m == "job_posted":
        msg = "Job posted successfully!"

    return templates.TemplateResponse(
        "thank_you.html",
        {
            "request": request,
            "message": msg
        }
    )

# ---------------- TERMS & PRIVACY ----------------
@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})