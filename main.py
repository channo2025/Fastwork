# main.py
# Win-Win Job — Digital Job Center (FastAPI + Jinja2)
# ✅ Demo mode (in-memory jobs + applications)
# ✅ Pages: home, jobs list, job detail, apply form, apply success, terms, privacy, about, contact, tasks, categories
# ✅ Static files: /static (style.css)

import os
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


# -------------------------
# App
# -------------------------
app = FastAPI(title="Win-Win Job")

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Branding
BRAND_NAME = "Win-Win Job"
BRAND_TAGLINE = "Fair jobs. Fast pay. Digital & simple."

# Make globals available in all templates (optional but handy)
templates.env.globals["BRAND_NAME"] = BRAND_NAME
templates.env.globals["BRAND_TAGLINE"] = BRAND_TAGLINE
templates.env.globals["YEAR"] = datetime.now().year


# -------------------------
# Demo data
# -------------------------
CATEGORIES: List[tuple] = [
    ("Cleaning", "🧽"),
    ("Moving help", "📦"),
    ("Yard work", "🌿"),
    ("Delivery", "🚚"),
    ("Handyman", "🛠️"),
    ("Babysitting", "👶"),
]

# In-memory demo jobs
DEMO_JOBS: List[Dict] = [
    {
        "id": 1,
        "title": "Move a couch",
        "city": "Portland, OR",
        "category": "Moving help",
        "pay": 60,
        "description": "Help move a couch from apartment to truck. 30–45 minutes. Two people job.",
        "created_at": "2026-01-01",
    },
    {
        "id": 2,
        "title": "Clean small studio",
        "city": "Vancouver, WA",
        "category": "Cleaning",
        "pay": 90,
        "description": "Deep clean a small studio (bathroom + kitchen). Cleaning supplies provided.",
        "created_at": "2026-01-02",
    },
    {
        "id": 3,
        "title": "Yard work: rake leaves",
        "city": "Beaverton, OR",
        "category": "Yard work",
        "pay": 55,
        "description": "Rake leaves + bag them. 1–2 hours depending on speed.",
        "created_at": "2026-01-03",
    },
]

# In-memory demo applications (later you'll store in PostgreSQL)
DEMO_APPLICATIONS: List[Dict] = []


# -------------------------
# Helpers
# -------------------------
def normalize(s: str) -> str:
    return (s or "").strip().lower()


def get_job_by_id(job_id: int) -> Optional[Dict]:
    for j in DEMO_JOBS:
        if int(j["id"]) == int(job_id):
            return j
    return None


def filter_jobs(q: str = "", city: str = "", category: str = "") -> List[Dict]:
    qn = normalize(q)
    cn = normalize(city)
    catn = normalize(category)

    out: List[Dict] = []
    for j in DEMO_JOBS:
        if qn and qn not in normalize(j["title"]) and qn not in normalize(j["description"]):
            continue
        if cn and cn not in normalize(j["city"]):
            continue
        if catn and catn != normalize(j["category"]):
            continue
        out.append(j)

    # newest first (simple)
    out.sort(key=lambda x: x.get("id", 0), reverse=True)
    return out


def next_job_id() -> int:
    if not DEMO_JOBS:
        return 1
    return max(int(j["id"]) for j in DEMO_JOBS) + 1


# -------------------------
# Basic pages
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # show a small subset of "featured" jobs (optional)
    featured = DEMO_JOBS[:2]
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "categories": CATEGORIES,
            "featured": featured,
        },
    )


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "categories": CATEGORIES},
    )


@app.get("/categories", response_class=HTMLResponse)
def categories_page(request: Request):
    return templates.TemplateResponse(
        "categories.html",
        {"request": request, "categories": CATEGORIES},
    )


@app.get("/jobs", response_class=HTMLResponse)
def jobs_list(
    request: Request,
    q: str = "",
    city: str = "",
    category: str = "",
):
    jobs = filter_jobs(q=q, city=city, category=category)
    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "jobs": jobs,
            "q": q,
            "city": city,
            "category": category,
            "categories": CATEGORIES,
        },
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job": job,
        },
    )


# -------------------------
# Apply flow
# -------------------------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_form(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    return templates.TemplateResponse(
        "apply.html",
        {
            "request": request,
            "job": job,
        },
    )


@app.post("/apply/{job_id}", response_class=HTMLResponse)
def apply_submit(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(""),
    message: str = Form(""),
):
    job = get_job_by_id(job_id)
    if not job:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    # DEMO save
    DEMO_APPLICATIONS.append(
        {
            "job_id": int(job_id),
            "full_name": full_name.strip(),
            "phone": phone.strip(),
            "email": (email or "").strip(),
            "message": (message or "").strip(),
            "created_at": datetime.utcnow().isoformat(),
        }
    )

    # Redirect to success page
    return RedirectResponse(url=f"/apply-success/{job_id}", status_code=303)


@app.get("/apply-success/{job_id}", response_class=HTMLResponse)
def apply_success(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    return templates.TemplateResponse(
        "apply_success.html",
        {
            "request": request,
            "job": job,
        },
    )


# -------------------------
# Post a job (demo)
# -------------------------
@app.get("/post", response_class=HTMLResponse)
def post_job_form(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {"request": request, "categories": CATEGORIES},
    )


@app.post("/post", response_class=HTMLResponse)
def post_job_submit(
    request: Request,
    title: str = Form(...),
    city: str = Form(...),
    category: str = Form(...),
    pay: int = Form(...),
    description: str = Form(...),
):
    # Basic validation
    if pay < 0:
        raise HTTPException(status_code=400, detail="Pay must be positive.")

    cat_names = [c[0] for c in CATEGORIES]
    if category not in cat_names:
        # allow custom but keep it consistent
        category = category.strip()

    new_job = {
        "id": next_job_id(),
        "title": title.strip(),
        "city": city.strip(),
        "category": category.strip(),
        "pay": int(pay),
        "description": description.strip(),
        "created_at": datetime.utcnow().date().isoformat(),
    }
    DEMO_JOBS.insert(0, new_job)

    return RedirectResponse(url=f"/jobs/{new_job['id']}", status_code=303)


# -------------------------
# Legal + info
# -------------------------
@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


# Optional thank you page (if you have it)
@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    return templates.TemplateResponse("thank_you.html", {"request": request})


# -------------------------
# 404
# -------------------------
@app.exception_handler(404)
def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


# -------------------------
# Local test helper
# -------------------------
# Run locally:
#   python -m venv .venv
#   source .venv/bin/activate
#   pip install -r requirements.txt
#   uvicorn main:app --reload
#
# Open:
#   http://127.0.0.1:8000