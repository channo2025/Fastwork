from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def common():
    return {"year": datetime.now().year}

@app.get("/jobs")
def jobs_page(request: Request, q: str = "", city: str = ""):
    # TODO: remplace par ton vrai fetch DB
    jobs = list_jobs(q=q, city=city)  # <= ta fonction
    ctx = {"request": request, "title":"Jobs", "jobs": jobs, "q": q, "city": city, **common()}
    return templates.TemplateResponse("jobs.html", ctx)

@app.get("/jobs/{job_id}")
def job_detail(request: Request, job_id: int):
    job = get_job(job_id)  # <= ta fonction
    ctx = {"request": request, "title": job["title"], "job": job, **common()}
    return templates.TemplateResponse("job_detail.html", ctx)

@app.post("/jobs/{job_id}/apply")
def apply_job(job_id: int,
              name: str = Form(...),
              phone_or_email: str = Form(...),
              message: str = Form("")):
    create_application(job_id, name, phone_or_email, message)  # <= ta fonction
    return RedirectResponse(url="/apply-success", status_code=303)

@app.get("/apply-success")
def apply_success(request: Request):
    return templates.TemplateResponse("apply_success.html", {"request": request, "title":"Success", **common()})

@app.get("/post")
def post_page(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request, "title":"Post a job", "error": None, **common()})

@app.post("/post")
def post_job(
    title: str = Form(...),
    city: str = Form(...),
    category: str = Form(...),
    pay_type: str = Form(...),
    pay_amount: float = Form(...),
    duration_hours: float | None = Form(None),
    description: str = Form(""),
    is_urgent: str | None = Form(None),
):
    create_job({
        "title": title,
        "city": city,
        "category": category,
        "pay_type": pay_type,
        "pay_amount": pay_amount,
        "duration_hours": duration_hours,
        "description": description,
        "is_urgent": True if is_urgent else False
    })  # <= ta fonction
    return RedirectResponse(url="/thank-you?m=Job+posted+successfully", status_code=303)

@app.get("/thank-you")
def thank_you(request: Request, m: str = "Thanks!"):
    return templates.TemplateResponse("thank_you.html", {"request": request, "title":"Thank you", "message": m, **common()})