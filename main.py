from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime

app = FastAPI()

# --------- Templates & static ---------
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --------- SIMPLE IN-MEMORY STORAGE ---------
# (Les jobs restent tant que le serveur ne redémarre pas)
tasks_data = []


# --------- HOME PAGE ---------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Page d'accueil : hero bleu + section "Available tasks near you".
    On envoie la liste des jobs à index.html.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tasks": tasks_data,
        },
    )


# --------- TASKS PAGE (liste complète) ---------
@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """
    Page /tasks : affiche tous les jobs postés sur JobDash.
    """
    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "tasks": tasks_data,
        },
    )


# --------- PAGE POST A JOB (GET) ---------
@app.get("/post-job", response_class=HTMLResponse)
async def post_job_form(request: Request):
    """
    Affiche le formulaire pour poster un job.
    """
    return templates.TemplateResponse(
        "post_job.html",
        {"request": request},
    )


# --------- TRAITEMENT POST A JOB (POST) ---------
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
    """
    Récupère les données du formulaire, crée un job en mémoire,
    l'ajoute dans tasks_data, puis affiche la page de confirmation.
    """
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

    return templates.TemplateResponse(
        "job_posted.html",  # ta page "Job posted 🎉"
        {
            "request": request,
            "job": job,
        },
    )


# --------- JOB DETAIL PAGE (/jobs/{job_id}) ---------
@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int):
    """
    Page de détails pour un job spécifique.
    URL : /jobs/1, /jobs/2, etc.
    """
    job = next((task for task in tasks_data if task["id"] == job_id), None)

    if not job:
        # Si l'ID n'existe pas → 404
        raise HTTPException(status_code=404, detail="Job not found")

    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job": job,
        },
    )