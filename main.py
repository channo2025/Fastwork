from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime

app = FastAPI()

# Templates directory
templates = Jinja2Templates(directory="templates")

# ---------- SIMPLE IN-MEMORY STORAGE ----------
# (Les jobs resteront tant que Render ne redémarre pas)
tasks_data = []


# ---------- HOME PAGE ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "tasks": tasks_data}
    )


# ---------- TASKS PAGE ----------
@app.get("/tasks", response_class=HTMLResponse)
def list_tasks(request: Request):
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "tasks": tasks_data}
    )


# ---------- TASK DETAIL ----------
@app.get("/task/{task_id}", response_class=HTMLResponse)
def task_detail(request: Request, task_id: int):
    task = next((t for t in tasks_data if t["id"] == task_id), None)
    if not task:
        return HTMLResponse("<h1>Task not found</h1>", status_code=404)

    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "task": task}
    )


# ---------- APPLY PAGE ----------
@app.get("/apply/{task_id}", response_class=HTMLResponse)
def apply(request: Request, task_id: int):
    task = next((t for t in tasks_data if t["id"] == task_id), None)
    if not task:
        return HTMLResponse("<h1>Task not found</h1>", status_code=404)

    return templates.TemplateResponse(
        "apply.html",
        {"request": request, "task": task}
    )


# ---------- DISPLAY POST JOB FORM ----------
@app.get("/post-job", response_class=HTMLResponse)
def post_job(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {"request": request}
    )


# ---------- SUBMIT JOB ----------
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
    # ID unique
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


# ---------- STATIC FILES ----------
app.mount("/static", StaticFiles(directory="static"), name="static")