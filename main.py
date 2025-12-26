from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Jobcenta")

# Templates
templates = Jinja2Templates(directory="templates")

# Static files (CSS, images, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --------------------
# HOME
# --------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# --------------------
# JOBS
# --------------------
@app.get("/jobs", response_class=HTMLResponse)
def jobs(request: Request):
    return templates.TemplateResponse("popular_tasks.html", {"request": request})

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "job_id": job_id}
    )

# --------------------
# APPLY
# --------------------
@app.get("/apply", response_class=HTMLResponse)
def apply_job(request: Request):
    return templates.TemplateResponse("apply_job.html", {"request": request})

@app.get("/apply/success", response_class=HTMLResponse)
def apply_success(request: Request):
    return templates.TemplateResponse("apply_success.html", {"request": request})

# --------------------
# POST JOB
# --------------------
@app.get("/post", response_class=HTMLResponse)
def post_job(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})

@app.get("/post/success", response_class=HTMLResponse)
def post_success(request: Request):
    return templates.TemplateResponse("post_success.html", {"request": request})

# --------------------
# STATIC PAGES
# --------------------
@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    return templates.TemplateResponse("thank_you.html", {"request": request})

# --------------------
# HEALTH CHECK (Render)
# --------------------
@app.get("/health")
def health():
    return {"status": "Jobcenta is running 🚀"}