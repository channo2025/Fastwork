from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Optional
from datetime import datetime

app = FastAPI(title="Win-Win Job")

# ✅ Static + templates (UNE SEULE FOIS)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

BRAND_NAME = "Win-Win Job"
BRAND_TAGLINE = "Fair jobs. Fast pay. Digital & simple."
BRAND_SUBTITLE = "Digital Job Center"

CATEGORIES = [
    ("Cleaning", "🧽"),
    ("Moving help", "📦"),
    ("Yard work", "🌿"),
    ("Delivery", "🚚"),
    ("Handyman", "🛠️"),
    ("Babysitting", "👶"),
]

# --- Demo in-memory DB ---
JOBS: List[Dict] = []
APPLICATIONS: List[Dict] = []

def _next_id(items: List[Dict]) -> int:
    return (max([it["id"] for it in items]) + 1) if items else 1

def _common_context(request: Request) -> Dict:
    return {
        "request": request,
        "brand_name": BRAND_NAME,
        "brand_tagline": BRAND_TAGLINE,
        "brand_subtitle": BRAND_SUBTITLE,
        "categories": CATEGORIES,
        "year": datetime.utcnow().year,
    }

@app.get("/health")
def health():
    return {"status": "Win-Win Job is running 🚀"}

# ---------------- Home ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    ctx = _common_context(request)
    ctx.update({"featured_jobs": JOBS[:6]})
    return templates.TemplateResponse("home.html", ctx)

# ---------------- Tasks (alias to Categories) ----------------
@app.get("/tasks", response_class=HTMLResponse)
def tasks(request: Request):
    ctx = _common_context(request)
    return templates.TemplateResponse("tasks.html", ctx)

@app.get("/categories", response_class=HTMLResponse)
def categories(request: Request):
    ctx = _common_context(request)
    return templates.TemplateResponse("categories.html", ctx)

# ---------------- Jobs list + detail ----------------
@app.get("/jobs", response_class=HTMLResponse)
def jobs(request: Request, q: Optional[str] = None, city: Optional[str] = None, category: Optional[str] = None):
    ctx = _common_context(request)
    filtered = JOBS

    if q:
        q_lower = q.lower()
        filtered = [j for j in filtered if q_lower in j["title"].lower() or q_lower in j["description"].lower()]

    if city:
        city_lower = city.lower()
        filtered = [j for j in filtered if city_lower in (j.get("city", "")).lower() or city_lower in (j.get("zip", "")).lower()]

    if category:
        filtered = [j for j in filtered if j.get("category") == category]

    ctx.update({"jobs": filtered, "q": q or "", "city": city or "", "category": category or ""})
    return templates.TemplateResponse("jobs.html", ctx)

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    job = next((j for j in JOBS if j["id"] == job_id), None)
    if not job:
        ctx = _common_context(request)
        ctx.update({"message": "Job not found."})
        return templates.TemplateResponse("404.html", ctx, status_code=404)

    ctx = _common_context(request)
    ctx.update({"job": job})
    return templates.TemplateResponse("job_detail.html", ctx)

# ---------------- Post a job (GET + POST) ----------------
@app.get("/post", response_class=HTMLResponse)
def post_job_form(request: Request):
    ctx = _common_context(request)
    return templates.TemplateResponse("post_job.html", ctx)

@app.post("/post", response_class=HTMLResponse)
def post_job_submit(
    request: Request,
    title: str = Form(...),
    category: str = Form(...),
    pay: str = Form(...),
    city: str = Form(""),
    zip: str = Form(""),
    description: str = Form(...),
    contact_name: str = Form(...),
    contact_phone: str = Form(""),
    contact_email: str = Form(""),
):
    job = {
        "id": _next_id(JOBS),
        "title": title.strip(),
        "category": category.strip(),
        "pay": pay.strip(),
        "city": city.strip(),
        "zip": zip.strip(),
        "description": description.strip(),
        "contact_name": contact_name.strip(),
        "contact_phone": contact_phone.strip(),
        "contact_email": contact_email.strip(),
        "created_at": datetime.utcnow().isoformat(),
    }
    JOBS.insert(0, job)  # newest first
    return RedirectResponse(url="/post/success", status_code=303)

@app.get("/post/success", response_class=HTMLResponse)
def post_success(request: Request):
    ctx = _common_context(request)
    return templates.TemplateResponse("post_success.html", ctx)

# ---------------- Apply (GET + POST) ----------------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_form(request: Request, job_id: int):
    job = next((j for j in JOBS if j["id"] == job_id), None)
    if not job:
        ctx = _common_context(request)
        return templates.TemplateResponse("apply_not_found.html", ctx, status_code=404)

    ctx = _common_context(request)
    ctx.update({"job": job})
    return templates.TemplateResponse("apply.html", ctx)

@app.post("/apply/{job_id}")
def apply_submit(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(""),
    message: str = Form(""),
):
    job = next((j for j in JOBS if j["id"] == job_id), None)
    if not job:
        return RedirectResponse(url="/apply/not-found", status_code=303)

    APPLICATIONS.insert(0, {
        "job_id": job_id,
        "full_name": full_name.strip(),
        "phone": phone.strip(),
        "email": email.strip(),
        "message": message.strip(),
        "created_at": datetime.utcnow().isoformat(),
    })

    return RedirectResponse(url="/apply/success", status_code=303)

@app.get("/apply/success", response_class=HTMLResponse)
def apply_success(request: Request):
    ctx = _common_context(request)
    return templates.TemplateResponse("apply_success.html", ctx)

@app.get("/apply/not-found", response_class=HTMLResponse)
def apply_not_found(request: Request):
    ctx = _common_context(request)
    return templates.TemplateResponse("apply_not_found.html", ctx, status_code=404)

# ---------------- Static pages ----------------
@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    ctx = _common_context(request)
    return templates.TemplateResponse("about.html", ctx)

@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    ctx = _common_context(request)
    return templates.TemplateResponse("contact.html", ctx)

@app.post("/contact")
def contact_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
):
    # demo: no email sending yet
    return RedirectResponse(url="/thank-you", status_code=303)

@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    ctx = _common_context(request)
    return templates.TemplateResponse("privacy.html", ctx)

@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    ctx = _common_context(request)
    return templates.TemplateResponse("terms.html", ctx)

@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    ctx = _common_context(request)
    return templates.TemplateResponse("thank_you.html", ctx)

# ---------------- 404 fallback ----------------
@app.exception_handler(404)
async def not_found(request: Request, exc):
    ctx = _common_context(request)
    ctx.update({"message": "Page not found."})
    return templates.TemplateResponse("404.html", ctx, status_code=404)