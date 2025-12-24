import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from sqlalchemy import create_engine, text

# ------------------------------------------------------------
# App + Templates + Static (IMPORTANT: app doit être défini AVANT mount)
# ------------------------------------------------------------
app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

static_dir = os.path.join(BASE_DIR, "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ------------------------------------------------------------
# DB: PostgreSQL on Render via DATABASE_URL
# fallback: local sqlite if DATABASE_URL absent
# ------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    # Render fournit souvent postgresql:// ; SQLAlchemy préfère postgresql+psycopg://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DATABASE_URL = "sqlite+pysqlite:///./baraconnect.db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def init_db():
    # Table jobs + applications (simple)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                city TEXT NOT NULL,
                pay TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """))

@app.on_event("startup")
def on_startup():
    init_db()

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def fetch_all_jobs(q: Optional[str] = None, city: Optional[str] = None):
    sql = "SELECT * FROM jobs"
    params = {}
    where = []
    if q:
        where.append("(LOWER(title) LIKE :q OR LOWER(description) LIKE :q OR LOWER(category) LIKE :q)")
        params["q"] = f"%{q.lower()}%"
    if city:
        where.append("LOWER(city) LIKE :city")
        params["city"] = f"%{city.lower()}%"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC"

    with engine.begin() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return rows

def fetch_job(job_id: int):
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM jobs WHERE id = :id"),
            {"id": job_id}
        ).mappings().first()
    return row

# ------------------------------------------------------------
# Routes (STABLE)
# ------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def home(request: Request):
    # HOME = index.html (si tu n'as pas ça -> Not Found)
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/jobs")
def jobs_page(request: Request, q: Optional[str] = None, city: Optional[str] = None):
    jobs = fetch_all_jobs(q=q, city=city)
    return templates.TemplateResponse("jobs.html", {"request": request, "jobs": jobs, "q": q or "", "city": city or ""})

@app.get("/job/{job_id}")
def job_detail(request: Request, job_id: int):
    job = fetch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})

@app.get("/post-job")
def post_job_form(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})

@app.post("/post-job")
def post_job_submit(
    title: str = Form(...),
    category: str = Form(...),
    city: str = Form(...),
    pay: str = Form(...),
    description: str = Form(...)
):
    created_at = datetime.utcnow().isoformat()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO jobs (title, category, city, pay, description, created_at)
            VALUES (:title, :category, :city, :pay, :description, :created_at)
        """), {
            "title": title,
            "category": category,
            "city": city,
            "pay": pay,
            "description": description,
            "created_at": created_at
        })

    # ✅ post-job -> job_posted (PAS apply-success)
    return RedirectResponse(url="/job-posted", status_code=303)

@app.get("/job-posted")
def job_posted(request: Request):
    return templates.TemplateResponse("job_posted.html", {"request": request})

@app.get("/apply/{job_id}")
def apply_form(request: Request, job_id: int):
    job = fetch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("apply.html", {"request": request, "job": job})

@app.post("/apply/{job_id}")
def apply_submit(
    job_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    message: str = Form("")
):
    job = fetch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    created_at = datetime.utcnow().isoformat()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO applications (job_id, full_name, email, phone, message, created_at)
            VALUES (:job_id, :full_name, :email, :phone, :message, :created_at)
        """), {
            "job_id": job_id,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "message": message or "",
            "created_at": created_at
        })

    # ✅ apply -> apply_success (PAS job-posted)
    return RedirectResponse(url=f"/apply-success?job_id={job_id}", status_code=303)

@app.get("/apply-success")
def apply_success(request: Request, job_id: Optional[int] = None):
    job = fetch_job(int(job_id)) if job_id else None
    return templates.TemplateResponse("apply_success.html", {"request": request, "job": job})