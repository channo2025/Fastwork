from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import List, Dict, Optional

app = FastAPI(title="Win-Win Job")

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# -----------------------
# Demo data (no database)
# -----------------------
CATEGORIES = [
    ("Cleaning", "🧽"),
    ("Moving help", "📦"),
    ("Yard work", "🌿"),
    ("Delivery", "🚚"),
    ("Handyman", "🛠️"),
    ("Babysitting", "👶"),
]

# simple in-memory list
JOBS: List[Dict] = [
    {
        "id": 1,
        "title": "Move a couch",
        "category": "Moving help",
        "city": "Portland, OR",
        "pay": 60,
        "description": "Need help moving a couch from apartment to truck. 45–60 minutes."
    },
    {
        "id": 2,
        "title": "Clean small studio",
        "category": "Cleaning",
        "city": "Vancouver, WA",
        "pay": 90,
        "description": "Deep clean a small studio (bathroom + kitchen). Supplies provided."
    },
]

def ctx(request: Request, **kwargs):
    base = {
        "request": request,
        "year": datetime.now().year,
        "categories": CATEGORIES,
    }
    base.update(kwargs)
    return base


# -----------------------
# Health
# -----------------------
@app.get("/health")
def health():
    return {"status": "Win-Win Job is running 🚀"}


# -----------------------
# Pages
# -----------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    featured = JOBS[:3]
    return templates.TemplateResponse("home.html", ctx(request, featured_jobs=featured))


@app.get("/categories", response_class=HTMLResponse)
def categories_page(request: Request):
    return templates.TemplateResponse("categories.html", ctx(request))


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    return templates.TemplateResponse("tasks.html", ctx(request))


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", ctx(request))


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", ctx(request))


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", ctx(request))


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse("terms.html", ctx(request))


@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    return templates.TemplateResponse("thank_you.html", ctx(request))


# -----------------------
# Jobs
# -----------------------
@app.get("/jobs", response_class=HTMLResponse)
def jobs_list(request: Request, q: Optional[str] = None, city: Optional[str] = None, category: Optional[str] = None):
    results = JOBS

    if q:
        qq = q.lower().strip()
        results = [j for j in results if qq in j["title"].lower() or qq in j["description"].lower()]

    if city:
        cc = city.lower().strip()
        results = [j for j in results if cc in j["city"].lower()]

    if category:
        results = [j for j in results if j["category"] == category]

    return templates.TemplateResponse("jobs.html", ctx(request, jobs=results, q=q or "", city=city or "", category=category or ""))


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    job = next((j for j in JOBS if j["id"] == job_id), None)
    if not job:
        return templates.TemplateResponse("404.html", ctx(request), status_code=404)
    return templates.TemplateResponse("job_detail.html", ctx(request, job=job))


# -----------------------
# Post a job
# -----------------------
@app.get("/post", response_class=HTMLResponse)
def post_job_form(request: Request):
    return templates.TemplateResponse("post_job.html", ctx(request))


@app.post("/post")
def post_job_submit(
    title: str = Form(...),
    category: str = Form(...),
    city: str = Form(...),
    pay: int = Form(...),
    description: str = Form(...),
):
    new_id = (max([j["id"] for j in JOBS]) + 1) if JOBS else 1
    JOBS.insert(0, {
        "id": new_id,
        "title": title,
        "category": category,
        "city": city,
        "pay": pay,
        "description": description,
    })
    return RedirectResponse(url="/post/success", status_code=303)


@app.get("/post/success", response_class=HTMLResponse)
def post_success(request: Request):
    return templates.TemplateResponse("post_success.html", ctx(request))


# -----------------------
# Apply
# -----------------------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_form(request: Request, job_id: int):
    job = next((j for j in JOBS if j["id"] == job_id), None)
    if not job:
        return templates.TemplateResponse("apply_not_found.html", ctx(request), status_code=404)
    return templates.TemplateResponse("apply.html", ctx(request, job=job))


@app.post("/apply/{job_id}")
def apply_submit(
    job_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    message: str = Form(""),
):
    # demo only (no DB)
    return RedirectResponse(url="/apply/success", status_code=303)


@app.get("/apply/success", response_class=HTMLResponse)
def apply_success(request: Request):
    return templates.TemplateResponse("apply_success.html", ctx(request))


# -----------------------
# Custom 404
# -----------------------
@app.exception_handler(404)
def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", ctx(request), status_code=404)