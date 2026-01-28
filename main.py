from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from typing import List, Dict, Optional
import os

app = FastAPI()

# Templates + Static
templates = Jinja2Templates(directory="templates")

if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Brand globals (safe)
BRAND_NAME = "Win-Win Job"
BRAND_TAGLINE = "Fair jobs. Fast pay. Digital & simple."
templates.env.globals["BRAND_NAME"] = BRAND_NAME
templates.env.globals["BRAND_TAGLINE"] = BRAND_TAGLINE


# ----------------------------
# DEMO DATA (remplace par DB plus tard)
# ----------------------------
CATEGORIES: List[Dict[str, str]] = [
    {"name": "Cleaning", "icon": "🧽"},
    {"name": "Moving help", "icon": "📦"},
    {"name": "Yard work", "icon": "🌿"},
    {"name": "Delivery", "icon": "🚗"},
    {"name": "Handyman", "icon": "🛠️"},
    {"name": "Babysitting", "icon": "🧸"},
]

JOBS: List[Dict[str, object]] = [
    {
        "id": 1,
        "title": "Move a couch",
        "city": "Portland, OR",
        "category": "Moving help",
        "pay": 60,
        "description": "Need help moving a couch from apartment to truck. 30–45 minutes.",
        "contact_name": "Client",
        "contact_phone": "(555) 123-4567",
    },
    {
        "id": 2,
        "title": "Clean small studio",
        "city": "Vancouver, WA",
        "category": "Cleaning",
        "pay": 90,
        "description": "Deep clean a small studio. Supplies provided. 2–3 hours.",
        "contact_name": "Client",
        "contact_phone": "(555) 222-3333",
    },
]

APPLICATIONS: List[Dict[str, object]] = []


def get_job_by_id(job_id: int) -> Optional[Dict[str, object]]:
    for j in JOBS:
        if int(j["id"]) == int(job_id):
            return j
    return None


def filter_jobs(q: str = "", city: str = "", category: str = "") -> List[Dict[str, object]]:
    q = (q or "").strip().lower()
    city = (city or "").strip().lower()
    category = (category or "").strip()

    out = []
    for j in JOBS:
        ok = True
        if q:
            ok = ok and (q in str(j["title"]).lower() or q in str(j["description"]).lower())
        if city:
            ok = ok and (city in str(j["city"]).lower())
        if category:
            ok = ok and (category == str(j["category"]))
        if ok:
            out.append(j)
    return out


# ----------------------------
# ROUTES
# ----------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Home = index.html
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categories": CATEGORIES,
            "jobs": JOBS[:6],  # petit extrait
        },
    )


@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request, q: str = "", city: str = "", category: str = ""):
    jobs = filter_jobs(q=q, city=city, category=category)
    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "jobs": jobs,
            "q": q,
            "city": city,
            "category": category,
            "categories": [(c["name"], c["icon"]) for c in CATEGORIES],
        },
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        return templates.TemplateResponse(
            "job_detail.html",
            {"request": request, "job": None, "job_id": job_id},
        )
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})


@app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_form(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        return templates.TemplateResponse("apply.html", {"request": request, "job": None, "job_id": job_id})
    return templates.TemplateResponse("apply.html", {"request": request, "job": job})


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
        # fallback safe (évite crash)
        return RedirectResponse(url="/jobs", status_code=303)

    APPLICATIONS.append(
        {
            "job_id": job_id,
            "full_name": full_name,
            "phone": phone,
            "email": email,
            "message": message,
        }
    )

    # IMPORTANT: redirection vers apply-success
    return RedirectResponse(url=f"/apply-success/{job_id}", status_code=303)


@app.get("/apply-success/{job_id}", response_class=HTMLResponse)
async def apply_success(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    return templates.TemplateResponse(
        "apply_success.html",
        {"request": request, "job": job, "job_id": job_id},
    )


@app.get("/post", response_class=HTMLResponse)
async def post_job_form(request: Request):
    return templates.TemplateResponse(
        "post.html",
        {"request": request, "categories": CATEGORIES},
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
):
    new_id = max([int(j["id"]) for j in JOBS] + [0]) + 1
    JOBS.insert(
        0,
        {
            "id": new_id,
            "title": title,
            "city": city,
            "category": category,
            "pay": int(pay),
            "description": description,
            "contact_name": contact_name or "Client",
            "contact_phone": contact_phone or "",
        },
    )
    return RedirectResponse(url=f"/post-success/{new_id}", status_code=303)


@app.get("/post-success/{job_id}", response_class=HTMLResponse)
async def post_success(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    return templates.TemplateResponse("post_success.html", {"request": request, "job": job, "job_id": job_id})


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