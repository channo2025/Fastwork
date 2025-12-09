from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime

app = FastAPI()

# Fichiers statiques (si tu as un dossier /static)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dossier des templates HTML
templates = Jinja2Templates(directory="templates")

# --------- STOCKAGE SIMPLE EN MÉMOIRE ----------
# (Les jobs disparaissent si Render redémarre)
tasks_data = []


# ------------ HOME PAGE ------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # On montre les jobs les plus récents en bas de la page
    latest_tasks = list(reversed(tasks_data))[:5]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tasks": latest_tasks,
        },
    )


# ------------ PAGE TOUTES LES TÂCHES -----------
@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "tasks": tasks_data,   # ⚠️ important : on envoie bien tasks_data
        },
    )


# ------------ FORMULAIRE POST A JOB ------------
@app.get("/post-job", response_class=HTMLResponse)
def show_post_job_form(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {"request": request},
    )


# ------------ TRAITEMENT DU FORMULAIRE ---------
@app.post("/post-job", response_class=HTMLResponse)
async def submit_job(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    budget: str = Form(...),
    when: str = Form(...),
    task_type: str = Form(...),
):
    # Créer un ID simple
    job_id = len(tasks_data) + 1

    job = {
        "id": job_id,
        "title": title,
        "description": description,
        "location": location,
        "budget": budget,
        "when": when,
        "task_type": task_type,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    tasks_data.append(job)

    # Page de confirmation (garde le nom que tu utilises déjà)
    return templates.TemplateResponse(
        "job_posted.html",   # si ton fichier s’appelle thank_you.html, change ici
        {
            "request": request,
            "job": job,
        },
    )


# ------------ DÉTAIL D’UN JOB ------------------
@app.get("/tasks/{job_id}", response_class=HTMLResponse)
def job_detail(job_id: int, request: Request):
    job = next((j for j in tasks_data if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job": job,
        },
    )