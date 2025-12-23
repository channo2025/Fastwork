from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
import sqlite3
import os
from datetime import datetime

APP_NAME = "BaraConnect"
DB_PATH = os.path.join("data", "baraconnect.db")

app = FastAPI(title=APP_NAME)

# CORS (si plus tard tu as un autre domaine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ---- Models ----
class JobCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    category: str = Field(..., min_length=2, max_length=30)   # Cleaning, Moving, Yard, Delivery...
    city: str = Field(..., min_length=2, max_length=40)
    pay_amount: float = Field(..., gt=0)
    pay_type: str = Field(..., min_length=2, max_length=20)   # "cash", "same-day", "hourly"
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

# ---- API ----
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
def apply_job(job_id: int, appy: ApplyCreate):
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
    """, (job_id, appy.name.strip(), appy.phone_or_email.strip(), (appy.message or "").strip(), now))
    conn.commit()
    conn.close()
    return {"ok": True, "message": "Application sent ✅"}

# ---- Serve the site (frontend) ----
# This makes "/" show static/index.html
app.mount("/", StaticFiles(directory="static", html=True), name="static")