from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "jobs.db"

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            price INTEGER NOT NULL,
            hours INTEGER NOT NULL,
            badge TEXT,
            client_name TEXT,
            description TEXT,
            contact_email TEXT NOT NULL,
            contact_sms TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # petite liste pour le bloc "Popular tasks"
    demo = [
        {"title": "Deep clean 1-bedroom", "location": "SE Portland", "price": 85},
        {"title": "Move boxes to storage", "location": "Gresham", "price": 60},
        {"title": "Yard mowing + cleanup", "location": "NE Portland", "price": 70},
        {"title": "Grocery shopping + drop-off", "location": "Downtown", "price": 45},
    ]
    return templates.TemplateResponse("index.html", {"request": request, "popular": demo})


# ---------------- TASKS ----------------
@app.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request):
    conn = db()
    jobs = conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
    conn.close()
    return templates.TemplateResponse("tasks.html", {"request": request, "jobs": jobs})


# ---------------- POST A JOB ----------------
@app.get("/post-job", response_class=HTMLResponse)
async def post_job_form(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request, "error": None})


@app.post("/post-job")
async def post_job_submit(
    request: Request,
    title: str = Form(...),
    location: str = Form(...),
    price: int = Form(...),
    hours: int = Form(...),
    badge: str = Form(""),
    client_name: str = Form(""),
    description: str = Form(""),
    contact_email: str = Form(...),
    contact_sms: str = Form("")
):
    conn = db()
    conn.execute("""
        INSERT INTO jobs (title, location, price, hours, badge, client_name, description, contact_email, contact_sms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, location, price, hours, badge, client_name, description, contact_email, contact_sms))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/tasks", status_code=303)


# ---------------- APPLY ----------------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_form(request: Request, job_id: int):
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if not job:
        return templates.TemplateResponse("apply.html", {"request": request, "job": None, "error": "Job not found."})
    return templates.TemplateResponse("apply.html", {"request": request, "job": job, "error": None})


@app.post("/apply/{job_id}")
async def apply_submit(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    message: str = Form("")
):
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return RedirectResponse(url="/tasks", status_code=303)

    conn.execute("""
        INSERT INTO applications (job_id, full_name, email, phone, message)
        VALUES (?, ?, ?, ?, ?)
    """, (job_id, full_name, email, phone, message))
    conn.commit()
    conn.close()

    return templates.TemplateResponse("apply_success.html", {"request": request, "job": job})


# ---------------- STATIC PAGES ----------------
@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})