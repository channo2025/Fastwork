from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER

app = FastAPI()

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Example jobs data (tu peux modifier plus tard) ---
jobs = [
    {
        "id": 1,
        "title": "House cleaning",
        "location": "Portland",
        "time": "3 hrs",
        "pay": 85,
        "description": "Clean a 1-bedroom apartment.",
    },
    {
        "id": 2,
        "title": "Move boxes to storage",
        "location": "Gresham",
        "time": "2 hrs",
        "pay": 60,
        "description": "Help move boxes into a storage unit.",
    },
]

def get_job(job_id: int):
    return next((j for j in jobs if j["id"] == job_id), None)

# ---------------- ROUTES ----------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "jobs": jobs})

@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    return templates.TemplateResponse("tasks.html", {"request": request, "jobs": jobs})

@app.get("/tasks/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        return templates.TemplateResponse("apply_not_found.html", {"request": request})
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})

@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_page(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        return templates.TemplateResponse("apply_not_found.html", {"request": request})
    return templates.TemplateResponse("apply.html", {"request": request, "job": job})

@app.post("/apply/{job_id}")
def submit_application(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
):
    job = get_job(job_id)
    if not job:
        return templates.TemplateResponse("apply_not_found.html", {"request": request})

    # Pour l’instant on “simule” l’envoi (plus tard on stockera en DB ou email)
    return RedirectResponse(url="/thank-you", status_code=HTTP_303_SEE_OTHER)

@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    return templates.TemplateResponse("thank_you.html", {"request": request})