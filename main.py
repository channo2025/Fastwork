from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3

app = FastAPI()

# Templates
templates = Jinja2Templates(directory="templates")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_NAME = "fastwork_db.db"


# -------------------------
# HOME
# -------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# -------------------------
# TASKS (LIST)
# -------------------------
@app.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request):
    conn = sqlite3.connect(DB_NAME)
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


# -------------------------
# POST JOB (FORM PAGE)
# -------------------------
@app.get("/post-job", response_class=HTMLResponse)
async def post_job_form(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {"request": request}
    )


# -------------------------
# POST JOB (SUBMIT)
# -------------------------
@app.post("/post-job")
async def post_job_submit(
    request: Request,
    title: str = Form(...),
    location: str = Form(...),
    price: str = Form(...),
    hours: str = Form(...),
    badge: str = Form(""),
    client: str = Form(""),
    description: str = Form(...),
    contact_email: str = Form(...),
    contact_sms: str = Form(...)
):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO job (
            title, location, price, hours, badge,
            client, description, contact_email, contact_sms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title, location, price, hours, badge,
        client, description, contact_email, contact_sms
    ))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/tasks", status_code=303)
    @app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_job(request: Request, job_id: int):
    return templates.TemplateResponse(
        "apply.html",
        {
            "request": request,
            "job_id": job_id
        }
    )