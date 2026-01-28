# main.py
import os
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException


APP_TITLE = "Win-Win Job"

app = FastAPI(title=APP_TITLE)

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Brand globals (available in all templates)
BRAND_NAME = "Win-Win Job"
BRAND_TAGLINE = "Fair jobs. Fast pay. Digital & simple."
templates.env.globals["BRAND_NAME"] = BRAND_NAME
templates.env.globals["BRAND_TAGLINE"] = BRAND_TAGLINE
templates.env.globals["YEAR"] = datetime.utcnow().year

# Categories used across pages
CATEGORIES = [
    ("Cleaning", "🧽"),
    ("Moving help", "📦"),
    ("Yard work", "🌿"),
    ("Delivery", "🚚"),
    ("Handyman", "🛠️"),
    ("Babysitting", "🧸"),
    ("Shopping & errands", "🛒"),
    ("Organizing", "🗂️"),
]
templates.env.globals["CATEGORIES"] = CATEGORIES


# ----------------------------
# Demo in-memory "DB"
# (You can swap later with PostgreSQL)
# ----------------------------
# Jobs
JOBS: List[Dict] = [
    {
        "id": 1,
        "title": "Move a couch",
        "city": "Portland, OR",
        "category": "Moving help",
        "pay": 60,
        "description": "Help move a couch from apartment to truck. 30–45 minutes.",
        "created_at": datetime.utcnow(),
        "contact_name": "Employer",
        "contact_phone": "(555) 111-2222",
        "contact_email": "employer@example.com",
    },
    {
        "id": 2,
        "title": "Clean small studio",
        "city": "Vancouver, WA",
        "category": "Cleaning",
        "pay": 90,
        "description": "Basic cleaning for a small studio: floors, kitchen, bathroom.",
        "created_at": datetime.utcnow(),
        "contact_name": "Employer",
        "contact_phone": "(555) 333-4444",
        "contact_email": "employer@example.com",
    },
]
NEXT_JOB_ID = max([j["id"] for j in JOBS], default=0) + 1

# Applications
APPLICATIONS: List[Dict] = []


def get_job_by_id(job_id: int) -> Optional[Dict]:
    for j in JOBS:
        if j["id"] == job_id:
            return j
    return None


def search_jobs(q: str = "", city: str = "", category: str = "") -> List[Dict]:
    q = (q or "").strip().lower()
    city = (city or "").strip().lower()
    category = (category or "").strip()

    results = JOBS[:]

    if q:
        results = [
            j for j in results
            if q in (j.get("title", "").lower() + " " + j.get("description", "").lower())
        ]
    if city:
        results = [j for j in results if city in (j.get("city", "").lower())]
    if category and category != "All":
        results = [j for j in results if j.get("category") == category]

    # newest first
    results.sort(key=lambda x: x.get("created_at", datetime.utcnow()), reverse=True)
    return results


# ----------------------------
# Error pages
# ----------------------------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Custom 404 page if exists
    if exc.status_code == 404 and os.path.exists(os.path.join("templates", "404.html")):
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    # fallback
    return HTMLResponse(f"{exc.status_code} - {exc.detail}", status_code=exc.status_code)


# ----------------------------
# Routes
# ----------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # optional: show a few categories/tasks in home
    popular_tasks = [
        "Cleaning & organizing",
        "Moving help",
        "Yard work",
        "Shopping & errands",
        "Handyman tasks",
    ]
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "popular_tasks": popular_tasks,
        },
    )


@app.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request):
    # If you have tasks.html; otherwise redirect to categories
    if os.path.exists(os.path.join("templates", "tasks.html")):
        return templates.TemplateResponse("tasks.html", {"request": request})
    return RedirectResponse(url="/categories", status_code=302)


@app.get("/categories", response_class=HTMLResponse)
async def categories(request: Request):
    # If you have categories.html; otherwise reuse jobs with category filters
    if os.path.exists(os.path.join("templates", "categories.html")):
        return templates.TemplateResponse("categories.html", {"request": request, "categories": CATEGORIES})
    return templates.TemplateResponse(
        "jobs.html",
        {"request": request, "jobs": search_jobs(), "q": "", "city": "", "category": "All", "categories": CATEGORIES},
    )


@app.get("/jobs", response_class=HTMLResponse)
async def jobs(request: Request, q: str = "", city: str = "", category: str = "All"):
    results = search_jobs(q=q, city=city, category=category)

    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "jobs": results,
            "q": q,
            "city": city,
            "category": category,
            "categories": CATEGORIES,
        },
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        # if you have a template apply_not_found.html you can reuse
        if os.path.exists(os.path.join("templates", "apply_not_found.html")):
            return templates.TemplateResponse("apply_not_found.html", {"request": request}, status_code=404)
        raise StarletteHTTPException(status_code=404, detail="Job not found")

    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job": job,
        },
    )


@app.get("/post", response_class=HTMLResponse)
async def post_job_form(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {
            "request": request,
            "categories": CATEGORIES,
        },
    )


@app.post("/post")
async def post_job_submit(
    request: Request,
    title: str = Form(...),
    city: str = Form(...),
    category: str = Form(...),
    pay: int = Form(...),
    description: str = Form(...),
    contact_name: str = Form(""),
    contact_phone: str = Form(""),
    contact_email: str = Form(""),
):
    global NEXT_JOB_ID

    job = {
        "id": NEXT_JOB_ID,
        "title": title.strip(),
        "city": city.strip(),
        "category": category.strip(),
        "pay": int(pay),
        "description": description.strip(),
        "created_at": datetime.utcnow(),
        "contact_name": contact_name.strip() or "Employer",
        "contact_phone": contact_phone.strip(),
        "contact_email": contact_email.strip(),
    }
    JOBS.append(job)
    NEXT_JOB_ID += 1

    # If you have post_success.html show it, else go to job detail
    if os.path.exists(os.path.join("templates", "post_success.html")):
        return templates.TemplateResponse(
            "post_success.html",
            {"request": request, "job": job},
        )
    return RedirectResponse(url=f"/jobs/{job['id']}", status_code=303)


@app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_form(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        if os.path.exists(os.path.join("templates", "apply_not_found.html")):
            return templates.TemplateResponse("apply_not_found.html", {"request": request}, status_code=404)
        raise StarletteHTTPException(status_code=404, detail="Job not found")

    return templates.TemplateResponse(
        "apply.html",
        {"request": request, "job": job},
    )


@app.post("/apply/{job_id}")
async def apply_submit(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(""),
    message: str = Form(""),
):
    job = get_job_by_id(job_id)
    if not job:
        raise StarletteHTTPException(status_code=404, detail="Job not found")

    APPLICATIONS.append(
        {
            "job_id": job_id,
            "full_name": full_name.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
            "message": message.strip(),
            "created_at": datetime.utcnow(),
        }
    )

    # Redirect to apply success (THIS MUST EXIST)
    return RedirectResponse(url=f"/apply-success/{job_id}", status_code=303)


@app.get("/apply-success/{job_id}", response_class=HTMLResponse)
async def apply_success(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    # even if job deleted, show generic success
    template_name = "apply_success.html" if os.path.exists(os.path.join("templates", "apply_success.html")) else "thank_you.html"

    # If neither exists, fallback HTML
    if not os.path.exists(os.path.join("templates", template_name)):
        return HTMLResponse("Application sent. Thank you!", status_code=200)

    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "job": job,
        },
    )


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


# Optional healthcheck
@app.get("/health")
async def health():
    return {"ok": True, "app": BRAND_NAME}