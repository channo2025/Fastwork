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
    datetime: str          # on garde en texte pour l’instant
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
# ROUTE HOME (index.html)
# -----------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session = Depends(get_session)):
    # Plus tard, on pourra afficher les vrais jobs ici
    statement = select(Job).order_by(Job.created_at.desc())
    jobs: List[Job] = session.exec(statement).all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jobs": jobs,
        },
    )


# -----------------------------
# ROUTES POST A JOB
# -----------------------------

# GET : afficher le formulaire
@app.get("/post-job", response_class=HTMLResponse)
async def show_post_job(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {
            "request": request,
            "submitted": False,
        },
    )


# POST : traiter le formulaire
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
    # Enregistrer le job en BDD
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

    # Ré-afficher la page avec message de succès
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