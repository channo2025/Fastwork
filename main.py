from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from datetime import datetime
from typing import List, Dict

app = FastAPI()

# Static folder (au cas où tu ajoutes des images / css plus tard)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Stockage simple en mémoire (jobs disparaissent si le serveur redémarre)
jobs: List[Dict] = []


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    latest_jobs = list(reversed(jobs[-5:]))  # derniers jobs
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "jobs": latest_jobs},
    )


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    # Tous les jobs, les plus récents en haut
    all_jobs = list(reversed(jobs))
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "jobs": all_jobs},
    )


@app.get("/tasks/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: str):
    job = next((j for j in jobs if j["id"] == job_id), None)
    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "job": job},
    )


@app.get("/post-job", response_class=HTMLResponse)
async def post_job_form(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {"request": request},
    )


@app.post("/post-job", response_class=HTMLResponse)
async def submit_job(
    request: Request,
    title: str = Form(...),
    category: str = Form(...),
    location: str = Form(...),
    pay: str = Form(...),
    pay_type: str = Form(...),
    description: str = Form(...),
):
    job = {
        "id": str(uuid4()),
        "title": title.strip(),
        "category": category.strip(),
        "location": location.strip(),
        "pay": pay.strip(),
        "pay_type": pay_type.strip(),
        "description": description.strip(),
        "created_at": datetime.utcnow(),
    }
    jobs.append(job)
    return RedirectResponse(url="/tasks", status_code=303)


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {"request": request},
    )


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request},
    )


@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    return templates.TemplateResponse(
        "terms.html",
        {"request": request},
    )


@app.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    return templates.TemplateResponse(
        "contact.html",
        {"request": request},
    )