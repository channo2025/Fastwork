from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3

app = FastAPI()

# Templates
templates = Jinja2Templates(directory="templates")

# Static files (CSS, images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------- HOME ----------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# ---------- TASKS ----------
@app.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request):
    conn = sqlite3.connect("fastwork_db.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM job ORDER BY id DESC")
    jobs = cur.fetchall()

    conn.close()

    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "jobs": jobs
        }
    )


# ---------- POST A JOB ----------
@app.get("/post-job", response_class=HTMLResponse)
async def post_job_form(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {"request": request}
    )


@app.post("/post-job")
async def post_job(
    title: str = Form(...),
    location: str = Form(...),
    price: str = Form(...),
    hours: str = Form(...),
    description: str = Form(...),
    contact_email: str = Form(...),
    contact_sms: str = Form(...)
):
    conn = sqlite3.connect("fastwork_db.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO job (title, location, price, hours, description, contact_email, contact_sms)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, location, price, hours, description, contact_email, contact_sms))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/tasks", status_code=303)


# ---------- APPLY ----------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_form(request: Request, job_id: int):
    return templates.TemplateResponse(
        "apply.html",
        {
            "request": request,
            "job_id": job_id
        }
    )


@app.post("/apply")
async def apply(
    job_id: int = Form(...),
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    conn = sqlite3.connect("fastwork_db.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO application (job_id, full_name, phone, email, message)
        VALUES (?, ?, ?, ?, ?)
    """, (job_id, full_name, phone, email, message))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/tasks", status_code=303)


# ---------- STATIC PAGES ----------
@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})