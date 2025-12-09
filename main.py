from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime

app = FastAPI()

# Static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# TEMP JOB STORAGE (in-memory)
tasks_data = []


# HOME PAGE
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "tasks": tasks_data}
    )


# TASK LIST PAGE
@app.get("/tasks", response_class=HTMLResponse)
def tasks(request: Request):
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "tasks": tasks_data}
    )


# POST JOB FORM PAGE
@app.get("/post-job", response_class=HTMLResponse)
def post_job_page(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


# HANDLE FORM SUBMISSION
@app.post("/post-job")
def submit_job(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    budget: str = Form(...),
    when: str = Form(...),
    task_type: str = Form(...)
):

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