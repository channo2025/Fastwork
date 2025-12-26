from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Static files (si tu as un dossier static/)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------------------
# HOME
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # IMPORTANT: on envoie jobs=[] pour éviter "jobs is undefined"
    return templates.TemplateResponse("home.html", {"request": request, "jobs": []})


# ---------------------------
# POPULAR TASKS / JOBS LIST
# ---------------------------
@app.get("/jobs", response_class=HTMLResponse)
def jobs_page(request: Request, q: str = "", city: str = ""):
    return templates.TemplateResponse(
        "popular_tasks.html",
        {"request": request, "jobs": [], "q": q, "city": city}
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    # sans DB, on met un job fake
    job = {
        "id": job_id,
        "title": "Sample job",
        "city": "Portland",
        "pay": "$80",
        "description": "This is a placeholder job. Next step is connecting the database."
    }
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})


# ---------------------------
# POST A JOB (GET + POST)
# ---------------------------
@app.get("/post", response_class=HTMLResponse)
def post_job_form(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


@app.post("/post")
def post_job_submit(
    request: Request,
    title: str = Form(...),
    city: str = Form(...),
    pay: str = Form(...),
    description: str = Form(...),
    contact_email: str = Form(None),
):
    # Ici: plus tard on enregistrera en DB.
    # Pour l’instant on redirige vers la page succès.
    return RedirectResponse(url="/post-success", status_code=303)


@app.get("/post-success", response_class=HTMLResponse)
def post_success(request: Request):
    return templates.TemplateResponse("post_success.html", {"request": request})


# ---------------------------
# APPLY (GET + POST)
# ---------------------------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_form(request: Request, job_id: int):
    return templates.TemplateResponse("apply_job.html", {"request": request, "job_id": job_id})


@app.post("/apply/{job_id}")
def apply_submit(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    message: str = Form(""),
):
    return RedirectResponse(url="/apply-success", status_code=303)


@app.get("/apply-success", response_class=HTMLResponse)
def apply_success(request: Request):
    return templates.TemplateResponse("apply_success.html", {"request": request})


# ---------------------------
# LEGAL / INFO PAGES
# ---------------------------
@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    return templates.TemplateResponse("thank_you.html", {"request": request})


# ---------------------------
# HEALTH CHECK
# ---------------------------
@app.get("/health")
def health():
    return {"status": "JOBCENTA is running 🚀"}