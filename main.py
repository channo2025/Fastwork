from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Optional
from datetime import datetime
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Win-Win Job")

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")



app.mount("/static", StaticFiles(directory="static"), name="static")

BRAND_NAME = "Win-Win Job"
BRAND_TAGLINE = "Fair jobs. Fast pay. Digital & simple."

CATEGORIES = [
    ("Cleaning", "🧽"),
    ("Moving help", "📦"),
    ("Yard work", "🌿"),
    ("Delivery", "🚚"),
    ("Handyman", "🛠"),
    ("Babysitting", "👶"),
    ("Packing", "📦"),
    ("Restaurant help", "🍽"),
    ("Events", "🎉"),
]

# -----------------------
# DEMO DATA (in-memory)
# -----------------------
# Each job: id, title, description, pay, location, when, category, phone, created_at
JOBS: List[Dict] = [
    {
        "id": 1,
        "title": "Apartment cleaning (2 hours)",
        "description": "Need help cleaning a small apartment. Bring gloves if possible.",
        "pay": 80,
        "location": "Houston 77084",
        "when": "Today 5pm",
        "category": "Cleaning",
        "contact_phone": "(000) 000-0000",
        "created_at": datetime.utcnow(),
    },
    {
        "id": 2,
        "title": "Moving help — loading boxes",
        "description": "Help loading boxes into a truck. Light/medium boxes.",
        "pay": 60,
        "location": "Portland 97205",
        "when": "Tomorrow 10am",
        "category": "Moving help",
        "contact_phone": "(000) 000-0000",
        "created_at": datetime.utcnow(),
    },
]

APPLICATIONS: List[Dict] = []  # stores applications in memory

def base_ctx(request: Request) -> Dict:
    return {
        "request": request,
        "brand_name": BRAND_NAME,
        "brand_tagline": BRAND_TAGLINE,
        "categories": CATEGORIES,
    }

def get_next_job_id() -> int:
    return (max([j["id"] for j in JOBS]) + 1) if JOBS else 1

def find_job(job_id: int) -> Optional[Dict]:
    for j in JOBS:
        if j["id"] == job_id:
            return j
    return None


# -----------------------
# PAGES
# -----------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    featured = sorted(JOBS, key=lambda x: x["id"], reverse=True)[:6]
    ctx = base_ctx(request)
    ctx.update({"featured_jobs": featured})
    return templates.TemplateResponse("index.html", ctx)


@app.get("/tasks", response_class=HTMLResponse)
def tasks(request: Request):
    ctx = base_ctx(request)
    return templates.TemplateResponse("tasks.html", ctx)


@app.get("/categories", response_class=HTMLResponse)
def categories_page(request: Request):
    ctx = base_ctx(request)
    return templates.TemplateResponse("categories.html", ctx)


@app.get("/jobs", response_class=HTMLResponse)
def jobs_page(request: Request, q: str = "", loc: str = ""):
    q_l = (q or "").strip().lower()
    loc_l = (loc or "").strip().lower()

    filtered = JOBS
    if q_l:
        filtered = [j for j in filtered if q_l in (j["title"] + " " + (j["description"] or "") + " " + j["category"]).lower()]
    if loc_l:
        filtered = [j for j in filtered if loc_l in (j["location"] or "").lower()]

    ctx = base_ctx(request)
    ctx.update({"jobs": sorted(filtered, key=lambda x: x["id"], reverse=True), "q": q, "loc": loc})
    return templates.TemplateResponse("jobs.html", ctx)


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    job = find_job(job_id)
    if not job:
        return RedirectResponse(url="/jobs", status_code=303)

    ctx = base_ctx(request)
    ctx.update({"job": job})
    return templates.TemplateResponse("job_detail.html", ctx)


# -----------------------
# POST A JOB
# -----------------------
@app.get("/post", response_class=HTMLResponse)
def post_job_form(request: Request):
    ctx = base_ctx(request)
    return templates.TemplateResponse("post_job.html", ctx)


@app.post("/post")
def post_job_submit(
    title: str = Form(...),
    description: str = Form(""),
    pay: int = Form(...),
    location: str = Form(...),
    when: str = Form(""),
    contact_phone: str = Form(...),
    category: str = Form("General"),
):
    new_job = {
        "id": get_next_job_id(),
        "title": title.strip(),
        "description": description.strip(),
        "pay": int(pay),
        "location": location.strip(),
        "when": when.strip(),
        "category": category.strip() if category.strip() else "General",
        "contact_phone": contact_phone.strip(),
        "created_at": datetime.utcnow(),
    }
    JOBS.append(new_job)
    return RedirectResponse(url="/post-success", status_code=303)


@app.get("/post-success", response_class=HTMLResponse)
def post_success(request: Request):
    ctx = base_ctx(request)
    return templates.TemplateResponse("post_success.html", ctx)


# -----------------------
# APPLY
# -----------------------
@app.get("/jobs/{job_id}/apply", response_class=HTMLResponse)
def apply_form(request: Request, job_id: int):
    job = find_job(job_id)
    if not job:
        return RedirectResponse(url="/jobs", status_code=303)

    ctx = base_ctx(request)
    ctx.update({"job": job})
    return templates.TemplateResponse("apply.html", ctx)


@app.post("/jobs/{job_id}/apply")
def apply_submit(
    job_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    message: str = Form(""),
):
    job = find_job(job_id)
    if not job:
        return RedirectResponse(url="/jobs", status_code=303)

    APPLICATIONS.append({
        "job_id": job_id,
        "name": name.strip(),
        "phone": phone.strip(),
        "message": message.strip(),
        "created_at": datetime.utcnow(),
    })

    return RedirectResponse(url="/apply-success", status_code=303)


@app.get("/apply-success", response_class=HTMLResponse)
def apply_success(request: Request):
    ctx = base_ctx(request)
    return templates.TemplateResponse("apply_success.html", ctx)


# -----------------------
# STATIC PAGES
# -----------------------
@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    ctx = base_ctx(request)
    return templates.TemplateResponse("about.html", ctx)

@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    ctx = base_ctx(request)
    return templates.TemplateResponse("contact.html", ctx)

@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    ctx = base_ctx(request)
    return templates.TemplateResponse("privacy.html", ctx)

@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    ctx = base_ctx(request)
    return templates.TemplateResponse("terms.html", ctx)

@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    ctx = base_ctx(request)
    return templates.TemplateResponse("thank_you.html", ctx)


# -----------------------
# health check (optional)
# -----------------------
@app.get("/health")
def health():
    return {"ok": True}