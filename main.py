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
# (Les jobs restent tant que le serveur Render ne redémarre pas)
tasks_data = []


# --------- HOME PAGE ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # On affiche seulement les jobs récents sur la home (par ex. 4 derniers)
    recent_tasks = list(reversed(tasks_data))[:4]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tasks": recent_tasks,
        },
    )


# --------- TASKS PAGE (ALL JOBS) ----------
@app.get("/tasks", response_class=HTMLResponse)
def all_tasks(request: Request):
    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "tasks": tasks_data,
        },
    )


# --------- POST JOB (FORM) ----------
@app.get("/post-job", response_class=HTMLResponse)
def post_job_form(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {
            "request": request,
        },
    )


# --------- HANDLE FORM SUBMIT ----------
@app.post("/post-job")
async def submit_job(
    request: Request,
    title: str = Form(...),
    category: str = Form(...),
    location: str = Form(...),
    pay: str = Form(...),
    pay_type: str = Form(...),
    when: str = Form(...),          # ✅ NOUVEAU CHAMP DATE + HEURE
    description: str = Form(...),
):
    # ID simple
    job_id = len(tasks_data) + 1

    tasks_data.append(
        {
            "id": job_id,
            "title": title,
            "category": category,
            "location": location,
            "pay": pay,
            "pay_type": pay_type,
            "when": when,  # ✅ enregistré
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
        }
    )

    # Après création, on envoie vers la page détails du job
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


# --------- ABOUT PAGE (si tu veux l'utiliser dans la nav) ----------
@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {"request": request},
    )