import os
import sqlite3
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

APP_NAME = "BaraConnect"
DB_PATH = os.path.join("data", "baraconnect.db")

# -------------------------
# App init (ORDER MATTERS)
# -------------------------
app = FastAPI(title=APP_NAME)

# Templates + Static
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS (ok for beta)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# DB helpers (SQLite)
# -------------------------
def db_conn():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        city TEXT NOT NULL,
        pay_amount REAL NOT NULL,
        pay_type TEXT NOT NULL,
        duration_hours REAL,
        description TEXT,
        contact TEXT,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        phone_or_email TEXT NOT NULL,
        message TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------------------------
# Pydantic Models
# -------------------------
class JobCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    category: str = Field(..., min_length=2, max_length=30)
    city: str = Field(..., min_length=2, max_length=40)
    pay_amount: float = Field(..., gt=0)
    pay_type: str = Field(..., min_length=2, max_length=20)  # cash, same-day, hourly, fixed
    duration_hours: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=600)
    contact: Optional[str] = Field(None, max_length=120)

class JobOut(BaseModel):
    id: int
    title: str
    category: str
    city: str
    pay_amount: float
    pay_type: str
    duration_hours: Optional[float] = None
    description: Optional[str] = None
    contact: Optional[str] = None
    created_at: str

class ApplyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    phone_or_email: str = Field(..., min_length=6, max_length=80)
    message: Optional[str] = Field(None, max_length=500)

# -------------------------
# Pages (same style via templates)
# -------------------------
@app.get("/")
def page_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/tasks")
def page_tasks(request: Request):
    return templates.TemplateResponse("tasks.html", {"request": request})

@app.get("/jobs")
def page_jobs(request: Request):
    return templates.TemplateResponse("jobs.html", {"request": request})

@app.get("/post")
def page_post(request: Request):
    return templates.TemplateResponse("post.html", {"request": request})

@app.get("/about")
def page_about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/contact")
def page_contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/terms")
def page_terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/privacy")
def page_privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

# -------------------------
# API
# -------------------------
@app.get("/api/health")
def health():
    return {"status": "BaraConnect API is running 🚀"}

@app.post("/api/jobs", response_model=JobOut)
def create_job(job: JobCreate):
    conn = db_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()

    cur.execute("""
        INSERT INTO jobs (title, category, city, pay_amount, pay_type, duration_hours, description, contact, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job.title.strip(),
        job.category.strip(),
        job.city.strip(),
        float(job.pay_amount),
        job.pay_type.strip().lower(),
        job.duration_hours,
        (job.description or "").strip(),
        (job.contact or "").strip(),
        now
    ))
    conn.commit()
    job_id = cur.lastrowid
    conn.close()

    return JobOut(
        id=job_id,
        title=job.title,
        category=job.category,
        city=job.city,
        pay_amount=job.pay_amount,
        pay_type=job.pay_type,
        duration_hours=job.duration_hours,
        description=job.description,
        contact=job.contact,
        created_at=now
    )

@app.get("/api/jobs", response_model=List[JobOut])
def list_jobs(
    q: Optional[str] = Query(None, description="search keyword"),
    city: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100)
):
    conn = db_conn()
    cur = conn.cursor()

    sql = "SELECT * FROM jobs"
    params = []
    where = []

    if q:
        where.append("(title LIKE ? OR description LIKE ? OR category LIKE ?)")
        kw = f"%{q}%"
        params += [kw, kw, kw]

    if city:
        where.append("city LIKE ?")
        params.append(f"%{city}%")

    if category:
        where.append("category LIKE ?")
        params.append(f"%{category}%")

    if where:
        sql += " WHERE " + " AND ".join(where)

    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return [JobOut(**dict(r)) for r in rows]

@app.get("/api/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobOut(**dict(row))

@app.post("/api/jobs/{job_id}/apply")
def apply_job(job_id: int, payload: ApplyCreate):
    conn = db_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM jobs WHERE id = ?", (job_id,))
    exists = cur.fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found")

    now = datetime.utcnow().isoformat()
    cur.execute("""
        INSERT INTO applications (job_id, name, phone_or_email, message, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        job_id,
        payload.name.strip(),
        payload.phone_or_email.strip(),
        (payload.message or "").strip(),
        now
    ))

    conn.commit()
    conn.close()
    return {"ok": True, "message": "Application sent ✅"}

# Optional: admin endpoint (basic) to view applications count
@app.get("/api/admin/applications_count")
def applications_count():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM applications")
    c = cur.fetchone()["c"]
    conn.close()
    return {"applications": c}