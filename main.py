import os
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()

# STATIC
app.mount("/static", StaticFiles(directory="static"), name="static")

# TEMPLATES
templates = Jinja2Templates(directory="templates")


def db_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(DATABASE_URL)


def init_db():
    """Create tables if not exist."""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    city TEXT NOT NULL,
                    pay TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS applications (
                    id SERIAL PRIMARY KEY,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    message TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
        conn.commit()


@app.on_event("startup")
def on_startup():
    init_db()


# -------------------------
# PAGES
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    popular = [
        {"name": "Cleaning", "tag": "Home & office cleaning"},
        {"name": "Moving", "tag": "Help moving & lifting"},
        {"name": "Yard work", "tag": "Garden & outdoor tasks"},
        {"name": "Delivery", "tag": "Local deliveries"},
        {"name": "Shopping", "tag": "Grocery & errands"},
        {"name": "Handyman", "tag": "Fixes & small repairs"},
    ]

    # latest jobs
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, category, city, pay, description FROM jobs ORDER BY created_at DESC LIMIT 6"
            )
            rows = cur.fetchall()

    jobs = []
    for r in rows:
        jobs.append(
            {
                "id": r[0],
                "title": r[1],
                "category": r[2],
                "city": r[3],
                "pay": r[4],
                "description": r[5],
            }
        )

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "popular": popular, "jobs": jobs},
    )


@app.get("/popular-tasks", response_class=HTMLResponse)
def popular_tasks(request: Request):
    popular = [
        {"name": "Cleaning", "tag": "Home & office cleaning"},
        {"name": "Moving", "tag": "Help moving & lifting"},
        {"name": "Yard work", "tag": "Garden & outdoor tasks"},
        {"name": "Delivery", "tag": "Local deliveries"},
        {"name": "Shopping", "tag": "Grocery & errands"},
        {"name": "Handyman", "tag": "Fixes & small repairs"},
    ]
    return templates.TemplateResponse("popular_tasks.html", {"request": request, "popular": popular})


@app.get("/jobs", response_class=HTMLResponse)
def jobs(request: Request, q: Optional[str] = None, city: Optional[str] = None):
    q = (q or "").strip()
    city = (city or "").strip()

    where = []
    params = []

    if q:
        where.append("(title ILIKE %s OR category ILIKE %s OR description ILIKE %s)")
        like = f"%{q}%"
        params += [like, like, like]
    if city:
        where.append("(city ILIKE %s)")
        params.append(f"%{city}%")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT id, title, category, city, pay, description FROM jobs {where_sql} ORDER BY created_at DESC",
                params,
            )
            rows = cur.fetchall()

    data = [
        {"id": r[0], "title": r[1], "category": r[2], "city": r[3], "pay": r[4], "description": r[5]}
        for r in rows
    ]
    return templates.TemplateResponse(
        "jobs.html",
        {"request": request, "jobs": data, "q": q, "city": city},
    )


@app.get("/job/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, category, city, pay, description FROM jobs WHERE id=%s", (job_id,))
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    job = {"id": row[0], "title": row[1], "category": row[2], "city": row[3], "pay": row[4], "description": row[5]}
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})


@app.get("/post-a-job", response_class=HTMLResponse)
def post_a_job(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


@app.post("/post-a-job")
def post_a_job_submit(
    title: str = Form(...),
    category: str = Form(...),
    city: str = Form(...),
    pay: str = Form(...),
    description: str = Form(...),
):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO jobs(title, category, city, pay, description) VALUES(%s,%s,%s,%s,%s)",
                (title.strip(), category.strip(), city.strip(), pay.strip(), description.strip()),
            )
        conn.commit()

    # ✅ page de succès dédiée au POST job
    return RedirectResponse(url="/thank-you?m=Job+posted+successfully", status_code=303)


@app.get("/apply", response_class=HTMLResponse)
def apply_page(request: Request, job_id: int):
    # check job exists
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, city, pay FROM jobs WHERE id=%s", (job_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    job = {"id": row[0], "title": row[1], "city": row[2], "pay": row[3]}
    return templates.TemplateResponse("apply.html", {"request": request, "job": job})


@app.post("/apply")
def apply_submit(
    job_id: int = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    message: str = Form(""),
):
    # Save application
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM jobs WHERE id=%s", (job_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Job not found")

            cur.execute(
                """
                INSERT INTO applications(job_id, full_name, email, phone, message)
                VALUES(%s,%s,%s,%s,%s)
                """,
                (job_id, full_name.strip(), email.strip(), phone.strip(), message.strip()),
            )
        conn.commit()

    # ✅ succès APPLY (PAS job posted)
    return RedirectResponse(url="/apply-success", status_code=303)


@app.get("/apply-success", response_class=HTMLResponse)
def apply_success(request: Request):
    return templates.TemplateResponse("apply_success.html", {"request": request})


@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request, m: str = "Done"):
    return templates.TemplateResponse("thank_you.html", {"request": request, "message": m})


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


# Custom 404 page (optional)
@app.exception_handler(404)
def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/apply-success")
def apply_success(request: Request):
    return templates.TemplateResponse("apply_success.html", {"request": request})

@app.get("/post-success")
def post_success(request: Request):
    return templates.TemplateResponse("post_success.html", {"request": request})