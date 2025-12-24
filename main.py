from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import Optional

app = FastAPI()

# ✅ Static + Templates (important: app doit exister AVANT mount)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ---------------------------
# ✅ MINI "DB" TEMPORAIRE (in-memory)
# Remplace plus tard par Postgres
# ---------------------------
JOBS = []
APPLICATIONS = []
JOB_ID = 1

def common_ctx(request: Request, title: str = "BaraConnect"):
    return {"request": request, "title": title, "year": datetime.now().year}

def list_jobs(q: str = "", city: str = ""):
    q = (q or "").strip().lower()
    city = (city or "").strip().lower()
    result = JOBS[:]
    if q:
        result = [j for j in result if q in j["title"].lower() or q in (j.get("description") or "").lower() or q in j.get("category","").lower()]
    if city:
        result = [j for j in result if city in j.get("city","").lower()]
    # latest first
    return sorted(result, key=lambda x: x["id"], reverse=True)

def get_job(job_id: int):
    for j in JOBS:
        if j["id"] == job_id:
            return j
    return None

def create_job(payload: dict):
    global JOB_ID
    payload["id"] = JOB_ID
    JOB_ID += 1
    JOBS.append(payload)
    return payload

def create_application(job_id: int, name: str, phone_or_email: str, message: str):
    APPLICATIONS.append({
        "job_id": job_id,
        "name": name,
        "phone_or_email": phone_or_email,
        "message": message,
        "created_at": datetime.now().isoformat()
    })


# ---------------------------
# ✅ PAGES (HTML)
# ---------------------------

@app.get("/")
def home(request: Request):
    # simple home -> tu peux afficher latest jobs sur home aussi si tu veux
    ctx = common_ctx(request, "BaraConnect")
    return templates.TemplateResponse("home.html", ctx)

@app.get("/jobs")
def jobs_page(request: Request, q: str = "", city: str = ""):
    jobs = list_jobs(q=q, city=city)
    ctx = common_ctx(request, "Jobs")
    ctx.update({"jobs": jobs, "q": q, "city": city})
    return templates.TemplateResponse("jobs.html", ctx)

@app.get("/jobs/{job_id}")
def job_detail_page(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        return templates.TemplateResponse("apply_not_found.html", {**common_ctx(request, "Not found")}, status_code=404)
    ctx = common_ctx(request, job["title"])
    ctx.update({"job": job})
    return templates.TemplateResponse("job_detail.html", ctx)

@app.get("/post")
def post_page(request: Request):
    ctx = common_ctx(request, "Post a job")
    ctx.update({"error": None})
    return templates.TemplateResponse("post_job.html", ctx)

@app.post("/post")
def post_job(
    title: str = Form(...),
    city: str = Form(...),
    category: str = Form(...),
    pay_type: str = Form(...),
    pay_amount: float = Form(...),
    duration_hours: Optional[float] = Form(None),
    description: str = Form(""),
    is_urgent: Optional[str] = Form(None),
):
    create_job({
        "title": title.strip(),
        "city": city.strip(),
        "category": category.strip(),
        "pay_type": pay_type.strip(),
        "pay_amount": float(pay_amount),
        "duration_hours": float(duration_hours) if duration_hours not in (None, "") else None,
        "description": description.strip(),
        "is_urgent": True if is_urgent else False
    })
    return RedirectResponse(url="/thank-you?m=Job+posted+successfully", status_code=303)

@app.post("/jobs/{job_id}/apply")
def apply_job(
    job_id: int,
    name: str = Form(...),
    phone_or_email: str = Form(...),
    message: str = Form(""),
):
    job = get_job(job_id)
    if not job:
        return RedirectResponse(url="/apply-not-found", status_code=303)

    create_application(job_id, name.strip(), phone_or_email.strip(), message.strip())
    return RedirectResponse(url="/apply-success", status_code=303)

from datetime import datetime

@app.get("/apply-success")
def apply_success(request: Request):
    return templates.TemplateResponse(
        "apply_success.html",
        {
            "request": request,
            "year": datetime.now().year,
            "title": "Application sent"
        }
    )

@app.get("/apply-not-found")
def apply_not_found(request: Request):
    return templates.TemplateResponse("apply_not_found.html", common_ctx(request, "Not found"), status_code=404)

@app.get("/thank-you")
def thank_you(request: Request, m: str = "Thanks!"):
    ctx = common_ctx(request, "Thank you")
    ctx.update({"message": m})
    return templates.TemplateResponse("thank_you.html", ctx)


# ---------------------------
# ✅ API (pour ton JS / future app)
# ---------------------------
API_PREFIX = "/api"

@app.get(f"{API_PREFIX}/jobs")
def api_list_jobs(q: str = "", city: str = ""):
    return JSONResponse(list_jobs(q=q, city=city))

@app.post(f"{API_PREFIX}/jobs")
def api_create_job(payload: dict):
    # expected keys like your JS:
    # title, city, category, pay_type, pay_amount, duration_hours, description, is_urgent
    job = create_job({
        "title": str(payload.get("title","")).strip(),
        "city": str(payload.get("city","")).strip(),
        "category": str(payload.get("category","")).strip(),
        "pay_type": str(payload.get("pay_type","flat")).strip(),
        "pay_amount": float(payload.get("pay_amount", 0) or 0),
        "duration_hours": payload.get("duration_hours", None),
        "description": str(payload.get("description","")).strip(),
        "is_urgent": bool(payload.get("is_urgent", False))
    })
    return JSONResponse(job)

@app.post(f"{API_PREFIX}/jobs/{{job_id}}/apply")
def api_apply(job_id: int, payload: dict):
    job = get_job(job_id)
    if not job:
        return JSONResponse({"error": "job not found"}, status_code=404)

    create_application(
        job_id,
        str(payload.get("name","")).strip(),
        str(payload.get("phone_or_email","")).strip(),
        str(payload.get("message","")).strip(),
    )
    return JSONResponse({"ok": True})