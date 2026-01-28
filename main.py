from __future__ import annotations

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Win-Win Job")

# -----------------------------
# Static + Templates (define ONCE)
# -----------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# -----------------------------
# HOME (index.html)
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -----------------------------
# CONTACT (contact.html) - GET + POST
# -----------------------------
@app.get("/contact", response_class=HTMLResponse)
async def contact_get(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request, "sent": False})


@app.post("/contact", response_class=HTMLResponse)
async def contact_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
):
    # For now: just show success message.
    # Later: you can store in DB or send email.
    return templates.TemplateResponse("contact.html", {"request": request, "sent": True})


# -----------------------------
# SIMPLE STATIC PAGES (keep your existing ones)
# -----------------------------
@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


# -----------------------------
# TASKS / CATEGORIES / JOBS (KEEP)
# Replace template names below if your files are named differently.
# -----------------------------
@app.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request):
    # If you have dynamic logic, keep it here.
    return templates.TemplateResponse("tasks.html", {"request": request})


@app.get("/categories", response_class=HTMLResponse)
async def categories(request: Request):
    return templates.TemplateResponse("categories.html", {"request": request})


@app.get("/jobs", response_class=HTMLResponse)
async def jobs(request: Request):
    return templates.TemplateResponse("jobs.html", {"request": request})

# ---------------------------
# POST A JOB (FORM PAGE)
# ---------------------------
@app.get("/post", response_class=HTMLResponse)
async def post_page(request: Request):
    return templates.TemplateResponse("post.html", {"request": request})


@app.post("/post")
async def post_submit(
    request: Request,
    title: str = Form(...),
    company: str = Form(...),
    city: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
):
    # ✅ plus tard tu mets ton code DB ici si tu veux
    job_id = "new"

    return RedirectResponse(url=f"/post-success/{job_id}", status_code=303)

from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

# ✅ GET: afficher le formulaire
@app.get("/post", response_class=HTMLResponse)
async def post_job_form(request: Request):
    # categories safe (si CATEGORIES existe déjà dans ton code, ça marche)
    categories = []
    try:
        # si tu as CATEGORIES = [(name, icon), ...]
        categories = CATEGORIES
    except Exception:
        categories = [("Cleaning", "🧽"), ("Moving help", "📦"), ("Yard work", "🌿"), ("Delivery", "🚚"), ("Handyman", "🛠️")]

    return templates.TemplateResponse(
        "post_job.html",
        {
            "request": request,
            "categories": categories,
        },
    )

# ✅ Alias si ton menu pointe vers /post-a-job
@app.get("/post-a-job", response_class=HTMLResponse)
async def post_job_form_alias(request: Request):
    return await post_job_form(request)

# ✅ POST: soumission du formulaire
@app.post("/post")
async def post_job_submit(
    request: Request,
    title: str = Form(...),
    city: str = Form(...),
    category: str = Form(...),
    pay: str = Form(...),
    description: str = Form(...),
):
    # IMPORTANT: ne crash pas même sans DB
    # Si tu as déjà une fonction DB create_job(), appelle-la ici.
    # Sinon, on redirige juste vers /jobs (ou /post-success si tu l’as).
    return RedirectResponse(url="/jobs", status_code=303)
# ---------------------------
# POST SUCCESS PAGE
# ---------------------------
@app.get("/post-success/{job_id}", response_class=HTMLResponse)
async def post_success(request: Request, job_id: str):
    return templates.TemplateResponse(
        "post_success.html",
        {
            "request": request,
            "job_id": job_id,
        }
    )
# -----------------------------
# APPLY (KEEP)
# Adjust template names to match your project.
# -----------------------------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_form(request: Request, job_id: str):
    return templates.TemplateResponse("apply.html", {"request": request, "job_id": job_id})


@app.post("/apply/{job_id}", response_class=HTMLResponse)
async dob_detail.html", {"request": request, "job_id": job_id})


# -----------------------------
# BASIC 404 PAGE (optional)
# -----------------------------
@app.exception_handler(404)
async def not_found(request: Request, exc):
    # if you have a template: 404.html
    try:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    except Exception:
        return HTMLResponse("<h1>404 Not Found</h1>", status_code=404)