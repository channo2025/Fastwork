from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime

app = FastAPI()

# Templates & static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --------- SIMPLE IN-MEMORY STORAGE ----------
tasks_data = []


# --------- HOME PAGE ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    recent_tasks = list(reversed(tasks_data))[:4]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "tasks": recent_tasks},
    )


# --------- TASKS PAGE (ALL JOBS) ----------
@app.get("/tasks", response_class=HTMLResponse)
def all_tasks(request: Request):
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "tasks": tasks_data},
    )


# --------- POST JOB (FORM) ----------
@app.get("/post-job", response_class=HTMLResponse)
def post_job_form(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {"request": request},
    )


@app.post("/post-job")
async def submit_job(
    request: Request,
    title: str = Form(...),
    category: str = Form(...),
    location: str = Form(...),
    pay: str = Form(...),
    pay_type: str = Form(...),
    when: str = Form(...),
    description: str = Form(...),
):
    job_id = len(tasks_data) + 1

    tasks_data.append(
        {
            "id": job_id,
            "title": title,
            "category": category,
            "location": location,
            "pay": pay,
            "pay_type": pay_type,
            "when": when,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
        }
    )

    return RedirectResponse(url=f"/jobs/{job_id}", status_code=303)


# --------- JOB DETAIL PAGE ----------
@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    job = next((j for j in tasks_data if j["id"] == job_id), None)
    if not job:
        return templates.TemplateResponse(
            "job_detail.html",
            {"request": request, "job": None},
            status_code=404,
        )

    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "job": job},
    )


# --------- ABOUT ----------
@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {"request": request},
    )


# --------- PRIVACY POLICY ----------
@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request},
    )


# --------- TERMS OF USE ----------
@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse(
        "terms.html",
        {"request": request},
    )


# --------- CONTACT ----------
@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse(
        "contact.html",
        {"request": request},
    )