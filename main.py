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


# -----------------------------
# POST A JOB (KEEP)
# If you already have DB logic, paste it back in these handlers.
# -----------------------------
@app.get("/post")
def post_job(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {
            "request": request,
            "form": None,
            "error": None
        }
    )

@app.post("/post", response_class=HTMLResponse)
async def post_job_submit(
    request: Request,
    title: str = Form(...),
    location: str = Form(...),
    pay: str = Form(...),
    description: str = Form(...),
):
    # TODO: save to DB later if you want.
    # For now show success page (adjust name if yours differs)
    return templates.TemplateResponse(
        "post_success.html",
        {"request": request, "title": title, "location": location, "pay": pay},
    )


# -----------------------------
# APPLY (KEEP)
# Adjust template names to match your project.
# -----------------------------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_form(request: Request, job_id: str):
    return templates.TemplateResponse("apply.html", {"request": request, "job_id": job_id})


@app.post("/apply/{job_id}", response_class=HTMLResponse)
async def apply_submit(
    request: Request,
    job_id: str,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    message: str = Form(...),
):
    # TODO: save to DB later if you want.
    return RedirectResponse(url=f"/apply-success/{job_id}", status_code=303)


@app.get("/apply-success/{job_id}", response_class=HTMLResponse)
async def apply_success(request: Request, job_id: str):
    return templates.TemplateResponse("apply_success.html", {"request": request, "job_id": job_id})


# -----------------------------
# JOB DETAIL (KEEP)
# -----------------------------
@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: str):
    return templates.TemplateResponse("job_detail.html", {"request": request, "job_id": job_id})


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