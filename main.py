from typing import Optional

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlmodel import SQLModel, Field, Session, create_engine, select

# -------------------------------------------------
# CONFIG BDD
# -------------------------------------------------

DATABASE_URL = "sqlite:///fastwork_db.db"
engine = create_engine(DATABASE_URL, echo=False)


# -------------------------------------------------
# MODÈLES
# -------------------------------------------------

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    title: str
    location: str
    price: int
    hours: str

    badge: Optional[str] = None
    client: Optional[str] = None
    description: Optional[str] = None

    # contact de l’employeur (pour plus tard)
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_sms: Optional[str] = None


class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    job_id: int
    full_name: str
    phone: str
    email: str
    message: str


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# -------------------------------------------------
# CONFIG FASTAPI + TEMPLATES + STATIC
# -------------------------------------------------

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# -------------------------------------------------
# PAGES PUBLIQUES
# -------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/jobs", response_class=HTMLResponse)
def list_jobs(
    request: Request,
    session: Session = Depends(get_session),
    location: Optional[str] = None,
    min_price: Optional[int] = None,
):
    statement = select(Job)

    if location:
        statement = statement.where(Job.location.ilike(f"%{location}%"))

    if min_price is not None:
        statement = statement.where(Job.price >= min_price)

    jobs = session.exec(statement).all()

    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "jobs": jobs,
            "location": location or "",
            "min_price": min_price or "",
        },
    )


@app.get("/job/{job_id}", response_class=HTMLResponse)
def job_detail(job_id: int, request: Request, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        return HTMLResponse("Job not found", status_code=404)

    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "job": job},
    )


# -------------------------------------------------
# FORMULAIRE CANDIDATURE
# -------------------------------------------------

@app.get("/job/{job_id}/apply", response_class=HTMLResponse)
def apply_form(job_id: int, request: Request, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        return HTMLResponse("Job introuvable", status_code=404)

    return templates.TemplateResponse(
        "apply.html",
        {"request": request, "job": job},
    )


# 👉 Ton NOUVEAU CODE ici
@app.post("/job/{job_id}/apply", response_class=HTMLResponse)
def apply_submit(
    job_id: int,
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    experience: str = Form(...),
    session: Session = Depends(get_session),
):
    job = session.get(Job, job_id)
    if not job:
        return HTMLResponse("Job introuvable", status_code=404)

    # (Optionnel) Enregistrer la candidature en BDD
    application = Application(
        job_id=job_id,
        full_name=full_name,
        phone=phone,
        email=email,
        message=experience,
    )
    session.add(application)
    session.commit()
    session.refresh(application)

    return templates.TemplateResponse(
        "apply_succes.html",
        {
            "request": request,
            "job": job,
            "full_name": full_name,
            "phone": phone,
            "email": email,
            "experience": experience,
            "application": application,
        },
    )


# -------------------------------------------------
# ADMIN – JOBS
# -------------------------------------------------

@app.get("/admin/jobs", response_class=HTMLResponse)
def admin_jobs(request: Request, session: Session = Depends(get_session)):
    jobs = session.exec(select(Job)).all()

    return templates.TemplateResponse(
        "admin_jobs.html",
        {"request": request, "jobs": jobs},
    )


@app.get("/post-job", response_class=HTMLResponse)
def post_job_form(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


@app.post("/post-job")
def post_job_submit(
    request: Request,
    title: str = Form(...),
    location: str = Form(...),
    price: int = Form(...),
    hours: str = Form(...),
    badge: Optional[str] = Form(None),
    client: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    contact_sms: Optional[str] = Form(None),
    session: Session = Depends(get_session),
):
    new_job = Job(
        title=title,
        location=location,
        price=price,
        hours=hours,
        badge=badge,
        client=client,
        description=description,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_sms=contact_sms,
    )
    session.add(new_job)
    session.commit()
    session.refresh(new_job)

    # Retour à la page admin des jobs
    return RedirectResponse(url="/admin/jobs", status_code=303)


# -------------------------------------------------
# ADMIN – CANDIDATURES
# -------------------------------------------------

@app.get("/admin/applications", response_class=HTMLResponse)
def admin_applications(request: Request, session: Session = Depends(get_session)):
    statement = select(Application, Job).where(Application.job_id == Job.id)
    rows = session.exec(statement).all()

@app.get("/post-job", response_class=HTMLResponse)
async def get_post_job(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


@app.post("/post-job", response_class=HTMLResponse)
async def submit_post_job(
    request: Request,
    title: str = Form(...),
    location: str = Form(...),
    budget: str = Form(None),
    date: str = Form(None),
    duration: str = Form(None),
    category: str = Form(None),
    details: str = Form(None),
    name: str = Form(None),
    email: str = Form(None),
):
    job = {
        "title": title,
        "location": location,
        "budget": budget,
        "details": details,
    }
    return templates.TemplateResponse(
        "post_job_success.html",
        {
            "request": request,
            "job": job,
        },
    )

    applications = []
    for application, job in rows:
        applications.append(
            {
                "id": application.id,
                "job_id": application.job_id,
                "job_title": job.title,
                "full_name": application.full_name,
                "phone": application.phone,
                "email": application.email,
                "message": application.message,
            }
        )

    return templates.TemplateResponse(
        "admin_applications.html",
        {
            "request": request,
            "applications": applications,
        },
    )

    @app.get("/post-job", response_class=HTMLResponse)
async def show_post_job(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {
            "request": request,
            "submitted": False,
        },
    )


@app.post("/post-job", response_class=HTMLResponse)
async def submit_post_job(
    request: Request,
    title: str = Form(...),
    details: str = Form(...),
    location: str = Form(...),
    budget: float = Form(...),
    datetime: str = Form(...),
    category: str = Form(...),
):
    # Ici pour l'instant on ne sauvegarde pas encore dans la base.
    # On affiche juste un message de succès avec les infos.
    return templates.TemplateResponse(
        "post_job.html",
        {
            "request": request,
            "submitted": True,
            "title": title,
            "details": details,
            "location": location,
            "budget": budget,
            "datetime": datetime,
            "category": category,
        },
    )