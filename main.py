import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER
from sqlalchemy import create_engine
 
app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
ENV = os.getenv("ENV", "production").lower()

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# --------------------
# Database
# --------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# --------------------
# Static + templates
# --------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -----------------------------
# DB Model
# -----------------------------
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(120), nullable=False)
    location = Column(String(120), nullable=False)
    pay = Column(String(50), nullable=False)        # ex: "$85" ou "85"
    when_text = Column(String(80), nullable=False)  # ex: "Today", "Tomorrow", "This weekend"
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables (safe)
Base.metadata.create_all(bind=engine)


# -----------------------------
# App + Templates
# -----------------------------
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def fetch_all_jobs(db):
    return db.query(Job).order_by(Job.created_at.desc()).all()


def fetch_popular_jobs(db, limit=3):
    return db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()


# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db = SessionLocal()
    try:
        popular = fetch_popular_jobs(db, limit=3)
    finally:
        db.close()

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "popular_jobs": popular}
    )


@app.get("/tasks", response_class=HTMLResponse)
def tasks(request: Request):
    db = SessionLocal()
    try:
        jobs = fetch_all_jobs(db)
    finally:
        db.close()

    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "jobs": jobs}
    )


@app.get("/post-a-job", response_class=HTMLResponse)
def post_job_page(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


@app.post("/post-a-job")
def post_job_submit(
    request: Request,
    title: str = Form(...),
    location: str = Form(...),
    pay: str = Form(...),
    when_text: str = Form(...)
):
    title = title.strip()
    location = location.strip()
    pay = pay.strip()
    when_text = when_text.strip()

    # mini validation
    if not title or not location or not pay or not when_text:
        return RedirectResponse(url="/post-a-job", status_code=HTTP_303_SEE_OTHER)

    db = SessionLocal()
    try:
        job = Job(
            title=title,
            location=location,
            pay=pay,
            when_text=when_text
        )
        db.add(job)
        db.commit()
    finally:
        db.close()

    return RedirectResponse(url="/thank-you", status_code=HTTP_303_SEE_OTHER)


@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    return templates.TemplateResponse("thank_you.html", {"request": request})


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