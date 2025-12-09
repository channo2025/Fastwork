from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime

app = FastAPI()

# -------------------------
# Static + Templates
# -------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -------------------------
# TEMPORARY TASK STORAGE
# (We add real DB later)
# -------------------------
tasks_data = []

# -------------------------
# HOME PAGE
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "tasks": tasks_data}
    )

# -------------------------
# TASK LIST PAGE
# -------------------------
@app.get("/tasks", response_class=HTMLResponse)
def tasks(request: Request):
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "tasks": tasks_data}
    )

# -------------------------
# POST JOB - DISPLAY FORM
# -------------------------
@app.get("/post-job", response_class=HTMLResponse)
def post_job_form(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})

# -------------------------
# POST JOB - FORM SUBMISSION
# -------------------------
@app.post("/post-job")
def submit_job(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    budget: float = Form(...),
    when: str = Form(...),
    task_type: str = Form(...)
):
    # Save new job
    tasks_data.append({
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

# -------------------------
# JOB DETAILS PAGE (OPTIONNEL POUR PLUS TARD)
# -------------------------
@app.get("/task/{task_id}", response_class=HTMLResponse)
def task_details(request: Request, task_id: int):
    if task_id < 0 or task_id >= len(tasks_data):
        return HTMLResponse("Job not found.", status_code=404)

    task = tasks_data[task_id]
    return templates.TemplateResponse(
        "task_details.html",
        {"request": request, "task": task}
    )