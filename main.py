from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlmodel import SQLModel, Field, Session, create_engine, select


# -----------------------------
# CONFIG BDD
# -----------------------------

DATABASE_URL = "sqlite:///fastwork_db.db"
engine = create_engine(DATABASE_URL, echo=False)


# -----------------------------
# MODÈLE JOB
# -----------------------------

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    details: str
    location: str
    budget: float
    datetime: str          # simple string pour l’instant
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# -----------------------------
# FONCTIONS BDD
# -----------------------------

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# -----------------------------
# CONFIG FASTAPI + TEMPLATES
# -----------------------------

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# -----------------------------
# ROUTES PAGES
# -----------------------------

# Home: index.html
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session = Depends(get_session)):
    # On récupère les jobs les plus récents (pour plus tard si tu veux les afficher)
    statement = select(Job).order_by(Job.created_at.desc())
    jobs: List[Job] = session.exec(statement).all()

    # index.html n’a pas besoin des jobs pour l’instant,
    # mais on les passe quand même si tu veux les utiliser plus tard.
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jobs": jobs,
        },
    )


# GET : afficher le formulaire Post a Job
@app.get("/post-job", response_class=HTMLResponse)
async def show_post_job(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {
            "request": request,
            "submitted": False,
        },
    )


# POST : traiter le formulaire Post a Job
@app.post("/post-job", response_class=HTMLResponse)
async def submit_post_job(
    request: Request,
    title: str = Form(...),
    details: str = Form(...),
    location: str = Form(...),
    budget: float = Form(...),
    datetime_value: str = Form(alias="datetime"),
    category: str = Form(...),
    session: Session = Depends(get_session),
):
    # On enregistre le job dans la BDD
    job = Job(
        title=title,
        details=details,
        location=location,
        budget=budget,
        datetime=datetime_value,
        category=category,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    # On renvoie la même page avec le message de succès
    return templates.TemplateResponse(
        "post_job.html",
        {
            "request": request,
            "submitted": True,
            "title": title,
            "details": details,
            "location": location,
            "budget": budget,
            "datetime": datetime_value,
            "category": category,
        },
    )


# (Optionnel) Liste des jobs sur une autre page si tu veux plus tard
@app.get("/jobs", response_class=HTMLResponse)
async def list_jobs(request: Request, session: Session = Depends(get_session)):
    statement = select(Job).order_by(Job.created_at.desc())
    jobs: List[Job] = session.exec(statement).all()
    return templates.TemplateResponse(
        "jobs.html",  # tu pourras créer ce template plus tard
        {
            "request": request,
            "jobs": jobs,
        },
    )