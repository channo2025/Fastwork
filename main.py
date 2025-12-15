from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Fake jobs list (replace with DB later)
jobs = [
    {"id": 1, "title": "Moving helper", "price": 200, "location": "Portland", "hours": 12, "badge": "Premium", "description": "helping moving", "contact_email": "email@example.com"},
    {"id": 2, "title": "Cleaning", "price": 85, "location": "SE Portland", "hours": 2, "badge": "Same-day", "description": "Deep clean 1-bedroom", "contact_email": "email@example.com"},
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request):
    return templates.TemplateResponse("tasks.html", {"request": request, "jobs": jobs})

@app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_page(request: Request, job_id: int):
    job = next((j for j in jobs if j["id"] == job_id), None)
    return templates.TemplateResponse("apply.html", {"request": request, "job": job})

@app.post("/apply/{job_id}", response_class=HTMLResponse)
async def apply_submit(
    request: Request,
    job_id: int,
    name: str = Form(...),
    contact: str = Form(...),
    message: str = Form("")
):
    return templates.TemplateResponse("thank_you.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})