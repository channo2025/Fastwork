from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import sqlite3
from datetime import datetime

app = FastAPI(title="Win-Win Job")

# Static + templates (UNE SEULE FOIS)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

BRAND_NAME = "Win-Win Job"
BRAND_TAGLINE = "Fair jobs. Fast pay. Digital & simple."

CATEGORIES = [
    ("Cleaning", "🧽"),
    ("Moving help", "📦"),
    ("Yard work", "🌿"),
    ("Delivery", "🚚"),
    ("Handyman", "🛠️"),
    ("Babysitting", "🧸"),
]

DB_PATH = "winwin.db"


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
            category TEXT NOT NULL,
            city TEXT NOT NULL,
            pay TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    """)
    conn.commit()
    conn.close()


init_db()


@app.get("/health")
def health():
    return {"status": "Win-Win Job is running 🚀"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # featured jobs (latest 5)
    conn = db()
    jobs = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    return templates.TemplateResponse("home.html", {
        "request": request,
        "brand_name": BRAND_NAME,
        "brand_tagline": BRAND_TAGLINE,
        "categories": CATEGORIES,
        "jobs": jobs,
    })


@app.get("/categories", response_class=HTMLResponse)
def categories_page(request: Request):
    return templates.TemplateResponse("categories.html", {
        "request": request,
        "brand_name": BRAND_NAME,
        "categories": CATEGORIES,
    })


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    # simple demo list
    tasks = [
        {"title": "Apartment cleaning", "category": "Cleaning", "pay": "$80", "city": "Portland"},
        {"title": "Move a couch", "category": "Moving help", "pay": "$60", "city": "San Diego"},
        {"title": "Yard trimming", "category": "Yard work", "pay": "$90", "city": "Houston"},
    ]
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "brand_name": BRAND_NAME,
        "tasks": tasks,
    })


@app.get("/jobs", response_class=HTMLResponse)
def jobs_list(request: Request, q: Optional[str] = None, city: Optional[str] = None):
    conn = db()
    sql = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if q:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if city:
        sql += " AND city LIKE ?"
        params += [f"%{city}%"]

    sql += " ORDER BY id DESC"
    jobs = conn.execute(sql, params).fetchall()
    conn.close()

    return templates.TemplateResponse("jobs.html", {
        "request": request,
        "brand_name": BRAND_NAME,
        "jobs": jobs,
        "q": q or "",
        "city": city or "",
    })


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()

    if not job:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    return templates.TemplateResponse("job_detail.html", {
        "request": request,
        "brand_name": BRAND_NAME,
        "job": job,
    })


@app.get("/post", response_class=HTMLResponse)
def post_job_form(request: Request):
    return templates.TemplateResponse("post_job.html", {
        "request": request,
        "brand_name": BRAND_NAME,
        "categories": CATEGORIES,
    })


@app.post("/post")
def post_job_submit(
    title: str = Form(...),
    category: str = Form(...),
    city: str = Form(...),
    pay: str = Form(...),
    description: str = Form(...)
):
    conn = db()
    conn.execute("""
        INSERT INTO jobs (title, category, city, pay, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, category, city, pay, description, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/post-success", status_code=303)


@app.get("/post-success", response_class=HTMLResponse)
def post_success(request: Request):
    return templates.TemplateResponse("post_success.html", {
        "request": request,
        "brand_name": BRAND_NAME,
    })


@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_form(request: Request, job_id: int):
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()

    if not job:
        return templates.TemplateResponse("apply_not_found.html", {"request": request}, status_code=404)

    return templates.TemplateResponse("apply.html", {
        "request": request,
        "brand_name": BRAND_NAME,
        "job": job,
    })


@app.post("/apply/{job_id}")
def apply_submit(
    job_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    message: str = Form("")
):
    conn = db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return RedirectResponse(url="/apply-not-found", status_code=303)

    conn.execute("""
        INSERT INTO applications (job_id, name, phone, message, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (job_id, name, phone, message, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/apply-success", status_code=303)


@app.get("/apply-success", response_class=HTMLResponse)
def apply_success(request: Request):
    return templates.TemplateResponse("apply_success.html", {
        "request": request,
        "brand_name": BRAND_NAME,
    })


@app.get("/apply-not-found", response_class=HTMLResponse)
def apply_not_found(request: Request):
    return templates.TemplateResponse("apply_not_found.html", {"request": request}, status_code=404)


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "brand_name": BRAND_NAME})


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request, "brand_name": BRAND_NAME})


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request, "brand_name": BRAND_NAME})


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request, "brand_name": BRAND_NAME})


@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    return templates.TemplateResponse("thank_you.html", {"request": request, "brand_name": BRAND_NAME})