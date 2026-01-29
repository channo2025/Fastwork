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
# In-memory demo data
# -----------------------------
@dataclass
class Job:
    id: int
    title: str
    city: str
    category: str
    pay: str
    description: str


@dataclass
class Application:
    id: int
    job_id: int
    full_name: str
    phone: str
    email: Optional[str]
    message: Optional[str]


JOB_SEQ = 3
APP_SEQ = 0

JOBS: Dict[int, Job] = {
    1: Job(
        id=1,
        title="Help move a couch",
        city="Portland, OR",
        category="Moving help",
        pay="120",
        description="Need help moving a couch from apartment to storage. 1–2 hours.",
    ),
    2: Job(
        id=2,
        title="House cleaning (2 hours)",
        city="Portland, OR",
        category="Cleaning",
        pay="80",
        description="General cleaning for small apartment. Bring your supplies if possible.",
    ),
    3: Job(
        id=3,
        title="Yard work / leaves",
        city="Vancouver, WA",
        category="Yard work",
        pay="100",
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


# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(request, ["index.html"], {"categories": CATEGORIES})


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
        },
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        return render(request, ["404.html"], {"message": "Job not found."})

    return render(request, ["job_detail.html"], {"job": asdict(job), "categories": CATEGORIES})


@app.get("/categories", response_class=HTMLResponse)
def categories_page(request: Request):
    return render(request, ["categories.html"], {"categories": CATEGORIES, "mode": "categories"})


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    # If you don't have tasks.html, we safely reuse categories.html
    return render(request, ["tasks.html", "categories.html"], {"categories": CATEGORIES, "mode": "tasks"})


@app.get("/post", response_class=HTMLResponse)
def post_job_form(request: Request):
    return render(request, ["post_job.html"], {"categories": CATEGORIES})


@app.post("/post")
def post_job_submit(
    request: Request,
    title: str = Form(...),
    city: str = Form(...),
    category: str = Form(...),
    pay: str = Form(...),
    description: str = Form(...),
):
    global JOB_SEQ
    JOB_SEQ += 1

    JOBS[JOB_SEQ] = Job(
        id=JOB_SEQ,
        title=title.strip(),
        city=city.strip(),
        category=category.strip(),
        pay=pay.strip().replace("$", ""),
        description=description.strip(),
    )

    return RedirectResponse(url=f"/jobs/{JOB_SEQ}", status_code=303)


@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_form(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        return render(
            request,
            ["apply_not_found.html", "404.html"],
            {"message": "This job no longer exists.", "job_id": job_id},
        )

    # We prefer apply_job.html (your main template)
    return render(request, ["apply_job.html", "apply.html", "applyy.html"], {"job": asdict(job)})


@app.post("/apply/{job_id}")
def apply_submit(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(""),
    message: str = Form(""),
):
    global APP_SEQ
    job = get_job(job_id)
    if not job:
        return RedirectResponse(url=f"/apply/{job_id}", status_code=303)

    APP_SEQ += 1
    APPLICATIONS.append(
        Application(
            id=APP_SEQ,
            job_id=job_id,
            full_name=full_name.strip(),
            phone=phone.strip(),
            email=email.strip() or None,
            message=message.strip() or None,
        )
    )

    return RedirectResponse(url=f"/apply-success/{job_id}", status_code=303)


@app.get("/apply-success/{job_id}", response_class=HTMLResponse)
def apply_success(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        return render(
            request,
            ["apply_not_found.html", "404.html"],
            {"message": "Application saved, but job not found.", "job_id": job_id},
        )

    return render(request, ["apply_success.html"], {"job": asdict(job)})


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