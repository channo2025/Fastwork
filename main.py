# main.py
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI(title="Win-Win Job")

# ----------------------------
# Static + Templates
# ----------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ----------------------------
# Brand / Globals (available in ALL templates)
# ----------------------------
BRAND_NAME = "Win-Win Job"
BRAND_TAGLINE = "Fair jobs. Fast pay. Digital & simple."

templates.env.globals["BRAND_NAME"] = BRAND_NAME
templates.env.globals["BRAND_TAGLINE"] = BRAND_TAGLINE
templates.env.globals["YEAR"] = datetime.now().year

# ----------------------------
# Demo Data (replace later with DB)
# ----------------------------
CATEGORIES = [
    ("Cleaning", "🧽"),
    ("Moving help", "📦"),
    ("Yard work", "🌿"),
    ("Delivery", "🚚"),
    ("Handyman", "🛠️"),
    ("Babysitting", "👶"),
]
templates.env.globals["CATEGORIES"] = CATEGORIES

# Demo jobs (in-memory)
JOBS: List[Dict] = [
    {
        "id": 1,
        "title": "Move a couch",
        "city": "Portland, OR",
        "category": "Moving help",
        "pay": 60,
        "description": "Help move a couch from apartment to truck. 30–45 minutes.",
        "created_at": datetime.now(),
    },
    {
        "id": 2,
        "title": "Clean small studio",
        "city": "Vancouver, WA",
        "category": "Cleaning",
        "pay": 90,
        "description": "Light cleaning (bathroom + kitchen). Supplies provided.",
        "created_at": datetime.now(),
    },
]

# Demo applications (in-memory)
APPLICATIONS: List[Dict] = []


def get_job_by_id(job_id: int) -> Optional[Dict]:
    for j in JOBS:
        if j["id"] == job_id:
            return j
    return None


def next_job_id() -> int:
    return (max([j["id"] for j in JOBS]) + 1) if JOBS else 1


# ----------------------------
# Error pages
# ----------------------------
@app.exception_handler(404)
async def custom_404(request: Request, exc: Exception):
    return templates.TemplateResponse(
        "404.html",
        {"request": request},
        status_code=404,
    )


# ----------------------------
# Pages
# ----------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # You want Popular categories on home (instead of Featured jobs)
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "categories": CATEGORIES,
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


@app.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request):
    # optional page if you have it
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "categories": CATEGORIES},
    )


@app.get("/categories", response_class=HTMLResponse)
async def categories_page(request: Request):
    return templates.TemplateResponse(
        "categories.html",
        {"request": request, "categories": CATEGORIES},
    )


# ----------------------------
# Jobs list + search/filter
# ----------------------------
@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(
    request: Request,
    q: str = "",
    city: str = "",
    category: str = "",
):
    q2 = (q or "").strip().lower()
    city2 = (city or "").strip().lower()
    category2 = (category or "").strip()

    filtered = JOBS[:]

    if q2:
        filtered = [
            j for j in filtered
            if q2 in (j["title"] or "").lower()
            or q2 in (j["description"] or "").lower()
            or q2 in (j["category"] or "").lower()
        ]

    if city2:
        filtered = [j for j in filtered if city2 in (j["city"] or "").lower()]

    if category2:
        filtered = [j for j in filtered if (j["category"] or "") == category2]

    # sort newest first (if created_at exists)
    filtered.sort(key=lambda x: x.get("created_at") or datetime.min, reverse=True)

    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "jobs": filtered,
            "q": q,
            "city": city,
            "category": category,
            "categories": CATEGORIES,
        },
    )


# ----------------------------
# Job detail
# ----------------------------
@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "job": job},
    )


# ----------------------------
# Apply: form
# ----------------------------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_form(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        # if you have apply_not_found.html use it, else 404
        return templates.TemplateResponse(
            "apply_not_found.html",
            {"request": request, "job_id": job_id},
            status_code=404,
        )

    return templates.TemplateResponse(
        "apply.html",
        {"request": request, "job": job},
    )


# ----------------------------
# Apply: submit (POST)
# IMPORTANT: 303 redirect so browser goes to GET page after POST
# ----------------------------
@app.post("/apply/{job_id}")
async def submit_application(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    phone: str = Form(...),
    email: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
):
    job = get_job_by_id(job_id)
    if not job:
        return RedirectResponse(url=f"/apply/{job_id}", status_code=303)

    APPLICATIONS.append(
        {
            "job_id": job_id,
            "full_name": full_name.strip(),
            "phone": phone.strip(),
            "email": (email or "").strip() or None,
            "message": (message or "").strip() or None,
            "created_at": datetime.now(),
        }
    )

    return RedirectResponse(url=f"/apply-success/{job_id}", status_code=303)


# ----------------------------
# Apply: success page (GET)
# ----------------------------
@app.get("/apply-success/{job_id}", response_class=HTMLResponse)
async def apply_success(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    return templates.TemplateResponse(
        "apply_success.html",
        {"request": request, "job": job, "job_id": job_id},
    )


# ----------------------------
# Post a job: form
# ----------------------------
@app.get("/post", response_class=HTMLResponse)
async def post_job_form(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {"request": request, "categories": CATEGORIES},
    )


# ----------------------------
# Post a job: submit (POST)
# ----------------------------
@app.post("/post")
async def post_job_submit(
    request: Request,
    title: str = Form(...),
    city: str = Form(...),
    category: str = Form(...),
    pay: int = Form(...),
    description: str = Form(...),
):
    title = title.strip()
    city = city.strip()
    category = category.strip()
    description = description.strip()

    if not title or not city or not category or not description:
        return RedirectResponse(url="/post", status_code=303)

    if category not in [c[0] for c in CATEGORIES]:
        return RedirectResponse(url="/post", status_code=303)

    JOBS.insert(
        0,
        {
            "id": next_job_id(),
            "title": title,
            "city": city,
            "category": category,
            "pay": int(pay),
            "description": description,
            "created_at": datetime.now(),
        },
    )

    return RedirectResponse(url="/post-success", status_code=303)


@app.get("/post-success", response_class=HTMLResponse)
async def post_success(request: Request):
    return templates.TemplateResponse("post_success.html", {"request": request})


# ----------------------------
# Health check (optional)
# ----------------------------
@app.get("/health")
async def health():
    return {"ok": True}