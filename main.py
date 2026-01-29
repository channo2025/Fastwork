from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()

# Static (css, images, js)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


# -----------------------------
# Helpers: safe template render
# -----------------------------
def template_exists(name: str) -> bool:
    try:
        templates.env.loader.get_source(templates.env, name)
        return True
    except Exception:
        return False


def render(request: Request, preferred: List[str], context: dict, status_code: int = 200) -> HTMLResponse:
    """
    Render the first template that exists from `preferred`.
    If none exists, render 404.html if available, else raise 404.
    """
    for t in preferred:
        if template_exists(t):
            return templates.TemplateResponse(t, {"request": request, **context}, status_code=status_code)

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
BRAND_TAGLINE = "Digital Job Center"

templates.env.globals["BRAND_NAME"] = BRAND_NAME
templates.env.globals["BRAND_TAGLINE"] = BRAND_TAGLINE


# -----------------------------
# In-memory demo data (safe)
# Replace later with DB
# -----------------------------
@dataclass
class Job:
    id: int
    title: str
    city: str
    category: str
    description: str
    pay: str = ""
    company: str = ""  # optional (some templates have it)


@dataclass
class Application:
    id: int
    job_id: int
    full_name: str
    phone: str
    email: Optional[str] = None
    message: Optional[str] = None


JOB_SEQ = 3
APP_SEQ = 0

JOBS: Dict[int, Job] = {
    1: Job(
        id=1,
        title="Help move a couch",
        city="Portland, OR",
        category="Moving help",
        pay="120",
        company="",
        description="Need help moving a couch from apartment to storage. 1–2 hours.",
    ),
    2: Job(
        id=2,
        title="House cleaning (2 hours)",
        city="Portland, OR",
        category="Cleaning",
        pay="80",
        company="",
        description="General cleaning for small apartment. Bring your supplies if possible.",
    ),
    3: Job(
        id=3,
        title="Yard work / leaves",
        city="Vancouver, WA",
        category="Yard work",
        pay="100",
        company="",
        description="Rake leaves + bagging. About 2 hours.",
    ),
}

APPLICATIONS: List[Application] = []

CATEGORIES = [
    ("Cleaning", "🧽"),
    ("Moving help", "📦"),
    ("Yard work", "🌿"),
    ("Delivery", "🚚"),
    ("Handyman", "🛠️"),
    ("Babysitting", "👶"),
    ("Shopping & errands", "🛒"),
]


def get_job(job_id: int) -> Optional[Job]:
    return JOBS.get(job_id)


def last_application_for_job(job_id: int) -> Optional[dict]:
    for app_ in reversed(APPLICATIONS):
        if app_.job_id == job_id:
            return asdict(app_)
    return None


# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # give templates more context to avoid crashes
    return render(
        request,
        ["index.html"],
        {
            "categories": CATEGORIES,
            "tasks": CATEGORIES,  # some templates call them tasks
            "popular_tasks": CATEGORIES,
        },
    )


@app.get("/jobs", response_class=HTMLResponse)
def jobs_list(request: Request, q: str = "", city: str = "", category: str = ""):
    all_jobs = list(JOBS.values())

    def match(job: Job) -> bool:
        if q and q.lower() not in (job.title + " " + job.description).lower():
            return False
        if city and city.lower() not in job.city.lower():
            return False
        if category and category.lower() != job.category.lower():
            return False
        return True

    filtered = [asdict(j) for j in all_jobs if match(j)]

    return render(
        request,
        ["jobs.html"],
        {
            "jobs": filtered,
            "q": q,
            "city": city,
            "category": category,
            "categories": CATEGORIES,
            "tasks": CATEGORIES,
        },
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        return render(request, ["404.html"], {"message": "Job not found."}, status_code=404)

    return render(
        request,
        ["job_detail.html"],
        {
            "job": asdict(job),
            "job_id": job_id,
            "categories": CATEGORIES,
            "tasks": CATEGORIES,
        },
    )


# Categories + Tasks
@app.get("/categories", response_class=HTMLResponse)
def categories_page(request: Request):
    return render(
        request,
        ["categories.html"],
        {
            "categories": CATEGORIES,
            "tasks": CATEGORIES,
            "mode": "categories",
        },
    )


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    # If tasks.html doesn't exist, reuse categories.html
    return render(
        request,
        ["tasks.html", "categories.html"],
        {
            "categories": CATEGORIES,
            "tasks": CATEGORIES,
            "mode": "tasks",
        },
    )


# Post a job
@app.get("/post", response_class=HTMLResponse)
def post_job_form(request: Request):
    return render(
        request,
        ["post_job.html"],
        {
            "categories": CATEGORIES,
            "tasks": CATEGORIES,
        },
    )


@app.post("/post")
def post_job_submit(
    request: Request,
    # required fields
    title: str = Form(...),
    city: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    # optional fields (templates differ)
    company: str = Form(""),
    pay: str = Form(""),
):
    global JOB_SEQ
    JOB_SEQ += 1

    pay_clean = (pay or "").strip().replace("$", "")
    company_clean = (company or "").strip()

    JOBS[JOB_SEQ] = Job(
        id=JOB_SEQ,
        title=title.strip(),
        city=city.strip(),
        category=category.strip(),
        description=description.strip(),
        pay=pay_clean,
        company=company_clean,
    )

    # Redirect to new job detail
    return RedirectResponse(url=f"/jobs/{JOB_SEQ}", status_code=303)


# Apply (GET)
@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_form(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        return render(
            request,
            ["apply_not_found.html", "404.html"],
            {"message": "This job no longer exists.", "job_id": job_id},
            status_code=404,
        )

    return render(
        request,
        ["apply_job.html", "apply.html", "applyy.html"],
        {
            "job": asdict(job),
            "job_id": job_id,
        },
    )

@app.post("/apply/{job_id}")
async def submit_application(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(None),
    message: str = Form(None),
):
    return RedirectResponse(url=f"/apply-success/{job_id}", status_code=303)


@app.get("/apply-success/{job_id}", response_class=HTMLResponse)
async def apply_success(request: Request, job_id: int):
    # récupère le job (selon ta fonction existante)
    job = None
    try:
        job = get_job_by_id(job_id)   # OU get_job(job_id) selon ton code
    except:
        job = None

    return templates.TemplateResponse(
        "apply_success.html",
        {"request": request, "job": job}
    )

# About / Contact
@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return render(request, ["about.html"], {})


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


# Terms / Privacy (souvent linkés dans base.html)
@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return render(request, ["terms.html"], {})


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return render(request, ["privacy.html"], {})


# Health check (Render)
@app.get("/health")
def health():
    return {"status": "ok"}


# 404 page
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if template_exists("404.html"):
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Page not found."},
            status_code=404,
        )
    return HTMLResponse("404 Not Found", status_code=404)


# 500 page (avoid blank white page)
@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    # If you have 500.html you can use it; otherwise show a simple HTML.
    if template_exists("500.html"):
        return templates.TemplateResponse(
            "500.html",
            {"request": request, "message": "Internal Server Error"},
            status_code=500,
        )
    return HTMLResponse(
        "<h2>Internal Server Error</h2><p>Something broke on the server. Check Render logs.</p>",
        status_code=500,
    )