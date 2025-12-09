from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# STATIC + TEMPLATES
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Liste en mémoire pour stocker les jobs postés
jobs = []


# ---------------------------
# HOME PAGE
# ---------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jobs": jobs,   # liste complète des jobs pour la section "Available tasks"
        },
    )


# ---------------------------
# TASKS PAGE (LISTE COMPLÈTE + FILTRES)
# ---------------------------
@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request, task_type: Optional[str] = None):
    # Filtrer par type si ?task_type=Cleaning par ex.
    if task_type:
        filtered_jobs = [
            job for job in jobs
            if job.get("task_type", "").lower() == task_type.lower()
        ]
    else:
        filtered_jobs = jobs

    # Liste de tous les types disponibles (pour les boutons de filtre)
    task_types = sorted({job["task_type"] for job in jobs if job.get("task_type")})

    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "jobs": filtered_jobs,
            "selected_type": task_type,
            "task_types": task_types,
        },
    )


# ---------------------------
# GET: POST A JOB (PAGE FORM)
# ---------------------------
@app.get("/post-job", response_class=HTMLResponse)
async def get_post_job(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


# ---------------------------
# POST: SUBMIT JOB
# ---------------------------
@app.post("/post-job", response_class=HTMLResponse)
async def submit_post_job(request: Request):
    form = await request.form()

    # On crée un job à partir du formulaire
    new_job = {
        "title": form.get("title", "").strip(),
        "description": form.get("description", "").strip(),
        "location": form.get("location", "").strip(),
        "budget": form.get("budget", "").strip(),
        "when": form.get("when", "").strip(),
        "task_type": form.get("task_type", "").strip(),
    }

    # On l'ajoute à la liste (en haut de la liste)
    if new_job["title"]:
        jobs.insert(0, new_job)

    print("\n===== NEW JOB POSTED =====")
    for k, v in new_job.items():
        print(f"{k}: {v}")
    print("==========================\n")

    # Page de confirmation
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>Job posted – JobDash</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background: white;
                padding: 30px 40px;
                border-radius: 16px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                text-align: center;
            }
            h1 { margin-bottom: 10px; }
            p { color: #555; margin-bottom: 20px; }
            a {
                display: inline-block;
                padding: 10px 18px;
                border-radius: 999px;
                text-decoration: none;
                background: #2563eb;
                color: white;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Job posted 🎉</h1>
            <p>Your task has been submitted successfully.</p>
            <a href="/">Back to home</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)
@app.get("/tasks", response_class=HTMLResponse)
def tasks(request: Request):
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "tasks": tasks_data}
    )