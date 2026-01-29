from __future__ import annotations

from dataclasses import asdict
from typing import List

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from crud import create_job, get_job, list_jobs, create_application


app = FastAPI()

# Static
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# -----------------------------
# Create tables at startup
# -----------------------------
@app.on_event("startup")
def _startup():
    Base.metadata.create_all(bind=engine)


# -----------------------------
# Helpers: safe template render
# -----------------------------
def template_exists(name: str) -> bool:
    try:
        templates.env.loader.get_source(templates.env, name)
        return True
    except Exception:
        return False


def render(request: Request, preferred: List[str], context: dict) -> HTMLResponse:
    for t in preferred:
        if template_exists(t):
            return templates.TemplateResponse(t, {"request": request, **context})

    if template_exists("404.html"):
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Page not found (template missing)."},
            status_code=404,
        )
    raise HTTPException(status_code=404, detail="Template not found")


# -----------------------------
# Branding (available in Jinja)
# -----------------------------
BRAND_NAME = "Win-Win Job"
BRAND_TAGLINE = "Fair jobs. Fast pay. Digital & simple."

templates.env.globals["BRAND_NAME"] = BRAND_NAME
templates.env.globals["BRAND_TAGLINE"] = BRAND_TAGLINE


# -----------------------------
# Categories (for UI)
# -----------------------------
CATEGORIES = [
    ("Cleaning", "🧽"),
    ("Moving help", "📦"),
    ("Yard work", "🌿"),
    ("Delivery", "🚚"),
    ("Handyman", "🛠️"),
    ("Babysitting", "👶"),
    ("Shopping & errands", "🛒"),
]


# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(request, ["index.html"], {"categories": CATEGORIES})


@app.get("/jobs", response_class=HTMLResponse)
def jobs_list_page(
    request: Request,
    q: str = "",
    city: str = "",
    category: str = "",
    db: Session = Depends(get_db),
):
    jobs = list_jobs(db, q=q, city=city, category=category)

    # templates might expect dicts
    jobs_dicts = [
        {
            "id": j.id,
            "title": j.title,
            "city": j.city,
            "category": j.category,
            "pay": j.pay,
            "description": j.description,
        }
        for j in jobs
    ]

    return render(
        request,
        ["jobs.html"],
        {
            "jobs": jobs_dicts,
            "q": q,
            "city": city,
            "category": category,
            "categories": CATEGORIES,
        },
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail_page(request: Request, job_id: int, db: Session = Depends(get_db)):
    job = get_job(db, job_id)
    if not job:
        return render(request, ["404.html"], {"message": "Job not found."})

    job_dict = {
        "id": job.id,
        "title": job.title,
        "city": job.city,
        "category": job.category,
        "pay": job.pay,
        "description": job.description,
    }

    return render(request, ["job_detail.html"], {"job": job_dict, "categories": CATEGORIES})


@app.get("/categories", response_class=HTMLResponse)
def categories_page(request: Request):
    return render(request, ["categories.html"], {"categories": CATEGORIES, "mode": "categories"})


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    # If you don't have tasks.html, reuse categories.html safely
    return render(request, ["tasks.html", "categories.html"], {"categories": CATEGORIES, "mode": "tasks"})


# -----------------------------
# Post a job
# -----------------------------
@app.get("/post", response_class=HTMLResponse)
def post_job_form(request: Request):
    return render(request, ["post_job.html"], {"categories": CATEGORIES})


@app.post("/post")
def post_job_submit(
    request: Request,
    title: str = Form(...),
    city: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    pay: str = Form(""),
    # Compatibility: if template still sends company, we ignore it
    company: str = Form("", include_in_schema=False),
    db: Session = Depends(get_db),
):
    job = create_job(db, title=title, city=city, category=category, pay=pay, description=description)
    return RedirectResponse(url=f"/jobs/{job.id}", status_code=303)


# -----------------------------
# Apply (GET)
# -----------------------------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_form(request: Request, job_id: int, db: Session = Depends(get_db)):
    job = get_job(db, job_id)
    if not job:
        return render(
            request,
            ["apply_not_found.html", "404.html"],
            {"message": "This job no longer exists.", "job_id": job_id},
        )

    job_dict = {
        "id": job.id,
        "title": job.title,
        "city": job.city,
        "category": job.category,
        "pay": job.pay,
        "description": job.description,
    }

    # Use the first apply template that exists
    return render(
        request,
        ["apply_job.html", "apply.html", "applyy.html"],
        {"job": job_dict},
    )


# -----------------------------
# Apply (POST) — super tolerant (fixes the crash)
# -----------------------------
@app.post("/apply/{job_id}")
def apply_submit(
    request: Request,
    job_id: int,
    # Some templates use name="full_name", others use name="name"
    full_name: str = Form(""),
    name: str = Form("", include_in_schema=False),
    # Some templates use phone required, some optional
    phone: str = Form(""),
    email: str = Form(""),
    message: str = Form(""),
    db: Session = Depends(get_db),
):
    job = get_job(db, job_id)
    if not job:
        return RedirectResponse(url=f"/apply/{job_id}", status_code=303)

    # pick whichever field is filled
    real_name = (full_name or "").strip() or (name or "").strip()
    real_phone = (phone or "").strip()

    # If missing required, just redirect back (no JSON crash)
    if not real_name or not real_phone:
        return RedirectResponse(url=f"/apply/{job_id}", status_code=303)

    create_application(
        db,
        job_id=job_id,
        full_name=real_name,
        phone=real_phone,
        email=email,
        message=message,
    )

    return RedirectResponse(url=f"/apply-success/{job_id}", status_code=303)


@app.get("/apply-success/{job_id}", response_class=HTMLResponse)
def apply_success(request: Request, job_id: int, db: Session = Depends(get_db)):
    job = get_job(db, job_id)
    if not job:
        return render(
            request,
            ["apply_not_found.html", "404.html"],
            {"message": "Application saved, but job not found.", "job_id": job_id},
        )

    job_dict = {
        "id": job.id,
        "title": job.title,
        "city": job.city,
        "category": job.category,
        "pay": job.pay,
        "description": job.description,
    }

    return render(request, ["apply_success.html"], {"job": job_dict})


# About
@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return render(request, ["about.html"], {})


# Contact
@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return render(request, ["contact.html"], {})


@app.post("/contact")
def contact_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
):
    return RedirectResponse(url="/contact/thank-you", status_code=303)


@app.get("/contact/thank-you", response_class=HTMLResponse)
def contact_thank_you(request: Request):
    return render(request, ["contact_thank_you.html"], {})


# Terms / Privacy (if templates exist)
@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return render(request, ["terms.html"], {})

@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return render(request, ["privacy.html"], {})


# Health check
@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if template_exists("404.html"):
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Page not found."},
            status_code=404,
        )
    return HTMLResponse("404 Not Found", status_code=404)