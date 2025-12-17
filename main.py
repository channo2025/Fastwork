from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER

app = FastAPI()

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Demo data (jobs) ---
jobs = [
    {
        "id": 1,
        "title": "House cleaning",
        "location": "Portland",
        "time": "3 hrs",
        "price": 85,
        "description": "Clean a 1-bedroom apartment.",
        "category": "Cleaning",
    },
    {
        "id": 2,
        "title": "Move boxes to storage",
        "location": "Gresham",
        "time": "2 hrs",
        "price": 60,
        "description": "Help move boxes to a storage unit.",
        "category": "Moving",
    },
]

# In-memory inbox (later: database / email)
applications = []
posted_jobs = []
contact_messages = []


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    popular = jobs[:4]
    return templates.TemplateResponse("index.html", {"request": request, "popular": popular})


@app.get("/tasks", response_class=HTMLResponse)
def tasks(request: Request):
    return templates.TemplateResponse("jobs.html", {"request": request, "jobs": jobs})


@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_page(request: Request, job_id: int):
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        return templates.TemplateResponse("thank_you.html", {"request": request, "title": "Job not found", "message": "This job is no longer available."})
    return templates.TemplateResponse("apply.html", {"request": request, "job": job})


@app.post("/apply/{job_id}")
def submit_application(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
):
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        return RedirectResponse(url="/thank-you", status_code=HTTP_303_SEE_OTHER)

    applications.append({
        "job_id": job_id,
        "full_name": full_name.strip(),
        "email": email.strip(),
        "message": message.strip(),
    })

    return RedirectResponse(url="/thank-you", status_code=HTTP_303_SEE_OTHER)


@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    return templates.TemplateResponse(
        "thank_you.html",
        {"request": request, "title": "Application received", "message": "Thanks! Your application was submitted. The client may contact you if selected."},
    )


# ----------------------------
# Post a job
# ----------------------------
@app.get("/post", response_class=HTMLResponse)
def post_job_page(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


@app.post("/post")
def submit_job_post(
    request: Request,
    title: str = Form(...),
    location: str = Form(...),
    time: str = Form(...),
    price: int = Form(...),
    description: str = Form(...),
    contact_email: str = Form(...),
):
    new_id = (max([j["id"] for j in jobs]) + 1) if jobs else 1
    job = {
        "id": new_id,
        "title": title.strip(),
        "location": location.strip(),
        "time": time.strip(),
        "price": int(price),
        "description": description.strip(),
        "category": "General",
        "contact_email": contact_email.strip(),
    }
    jobs.insert(0, job)
    posted_jobs.append(job)

    return RedirectResponse(url="/post/thank-you", status_code=HTTP_303_SEE_OTHER)


@app.get("/post/thank-you", response_class=HTMLResponse)
def post_job_thank_you(request: Request):
    return templates.TemplateResponse("post_job_thank_you.html", {"request": request})


# ----------------------------
# Info pages
# ----------------------------
@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


# ----------------------------
# Contact
# ----------------------------
@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.post("/contact")
def submit_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
):
    contact_messages.append({
        "name": name.strip(),
        "email": email.strip(),
        "message": message.strip(),
    })
    return RedirectResponse(url="/contact/thank-you", status_code=HTTP_303_SEE_OTHER)


@app.get("/contact/thank-you", response_class=HTMLResponse)
def contact_thank_you(request: Request):
    return templates.TemplateResponse(
        "contact_thank_you.html",
        {"request": request, "title": "Message sent", "message": "Thanks! We received your message and will reply if needed."},
    )