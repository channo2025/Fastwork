from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Fake jobs (TEMPORAIRE mais STABLE)
JOBS = [
    {
        "id": 1,
        "title": "House cleaning",
        "price": 85,
        "location": "Portland",
        "hours": 3,
        "description": "Clean a 1-bedroom apartment."
    },
    {
        "id": 2,
        "title": "Move boxes",
        "price": 60,
        "location": "Gresham",
        "hours": 2,
        "description": "Help move boxes to storage."
    }
]

@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_page(request: Request, job_id: int):
    job = next((j for j in JOBS if j["id"] == job_id), None)

    if not job:
        return HTMLResponse("<h1>Job not found</h1>", status_code=404)

    return templates.TemplateResponse(
        "apply.html",
        {"request": request, "job": job}
    )