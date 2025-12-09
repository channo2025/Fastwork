from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime

app = FastAPI()

# ---------- STATIC & TEMPLATES ----------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---------- TEMP STORAGE FOR JOBS ----------
# (pour l'instant, on garde les jobs en mémoire)
tasks_data = []


# ---------- HOME PAGE ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "tasks": tasks_data}
    )


# ---------- TASKS LIST PAGE (/tasks) ----------
@app.get("/tasks", response_class=HTMLResponse)
def tasks(request: Request):
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "tasks": tasks_data}
    )


# ---------- POST JOB FORM (GET) ----------
@app.get("/post-job", response_class=HTMLResponse)
def post_job_page(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


# ---------- POST JOB FORM (POST) ----------
@app.post("/post-job", response_class=HTMLResponse)
def submit_job(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    budget: str = Form(...),
    when: str = Form(...),
    task_type: str = Form(...)
):
    # Simple ID pour plus tard (détails)
    job_id = len(tasks_data) + 1

    tasks_data.append({
        "id": job_id,
        "title": title,
        "description": description,
        "location": location,
        "budget": budget,
        "when": when,
        "task_type": task_type,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    return templates.TemplateResponse(
        "job_posted.html",
        {"request": request}
    )