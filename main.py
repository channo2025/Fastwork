from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime

app = FastAPI(title="Win-Win Job")

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

BRAND_NAME = "Win-Win Job"
BRAND_TAGLINE = "Fair jobs. Fast pay. Digital & simple."

CATEGORIES = [
    ("Cleaning", "🧽"),
    ("Moving help", "📦"),
    ("Yard work", "🌿"),
    ("Delivery", "🚚"),
    ("Handyman", "🛠️"),
    ("Babysitting", "🧒"),
]

DB_PATH = "fastwork_db.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            city TEXT NOT NULL,
            pay INTEGER NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_jobs(q: str = "", city: str = "", category: str = ""):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if q:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]

    if city:
        query += " AND city LIKE ?"
        params += [f"%{city}%"]

    if category:
        query += " AND category = ?"
        params += [category]

    query += " ORDER BY id DESC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_job(job_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "Win-Win Job is running 🚀"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "brand_name": BRAND_NAME,
            "brand_tagline": BRAND_TAGLINE,
            "categories": CATEGORIES,
        },
    )


@app.get("/tasks", response_class=HTMLResponse)
def tasks(request: Request):
    return templates.TemplateResponse(
        "tasks.html",
        {"request": request, "brand_name": BRAND_NAME, "categories": CATEGORIES},
    )


@app.get("/categories", response_class=HTMLResponse)
def categories_page(request: Request):
    return templates.TemplateResponse(
        "categories.html",
        {"request": request, "brand_name": BRAND_NAME, "categories": CATEGORIES},
    )


@app.get("/jobs", response_class=HTMLResponse)
def jobs(
    request: Request,
    q: str = "",
    city: str = "",
    category: str = "",
):
    items = get_jobs(q=q, city=city, category=category)
    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "brand_name": BRAND_NAME,
            "jobs": items,
            "q": q,
            "city": city,
            "category": category,
            "categories": CATEGORIES,
        },
    )


@app.get("/post", response_class=HTMLResponse)
def post_form(request: Request):
    return templates.TemplateResponse(
        "post_job.html",
        {"request": request, "brand_name": BRAND_NAME, "categories": CATEGORIES},
    )


@app.post("/post")
def post_submit(
    title: str = Form(...),
    category: str = Form(...),
    city: str = Form(...),
    pay: int = Form(...),
    description: str = Form(...),
):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO jobs (title, category, city, pay, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (title, category, city, pay, description, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/thank-you", status_code=303)


@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request):
    return templates.TemplateResponse(
        "thank_you.html",
        {"request": request, "brand_name": BRAND_NAME},
    )


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {"request": request, "brand_name": BRAND_NAME},
    )


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse(
        "contact.html",
        {"request": request, "brand_name": BRAND_NAME},
    )


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request, "brand_name": BRAND_NAME},
    )


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse(
        "terms.html",
        {"request": request, "brand_name": BRAND_NAME},
    )


@app.exception_handler(404)
def custom_404(request: Request, exc):
    return templates.TemplateResponse(
        "404.html",
        {"request": request, "brand_name": BRAND_NAME},
        status_code=404,
    )

# ---------- Job details ----------
@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_details(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "brand_name": BRAND_NAME},
            status_code=404
        )

    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "brand_name": BRAND_NAME,
            "job": job,
        },
    )

# ---------- Apply ----------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_form(request: Request, job_id: int):
    job = get_job(job_id)
    if not job:
        return templates.TemplateResponse(
            "apply_not_found.html",
            {"request": request, "brand_name": BRAND_NAME},
            status_code=404
        )

    return templates.TemplateResponse(
        "apply.html",
        {
            "request": request,
            "brand_name": BRAND_NAME,
            "job": job,
        },
    )

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Win-Win Job")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

BRAND_NAME = "Win-Win Job"
BRAND_TAGLINE = "Fair jobs. Fast pay. Digital & simple."

# ✅ Optionnel mais PRO: rendre BRAND_NAME dispo partout sans le repasser
templates.env.globals["BRAND_NAME"] = BRAND_NAME
templates.env.globals["BRAND_TAGLINE"] = BRAND_TAGLINE


# ----------------------------
# Helpers DB (adapte à ton code)
# ----------------------------
def get_job_by_id(job_id: int):
    """
    IMPORTANT: remplace le contenu par TA fonction DB.
    Doit retourner un dict ou None.
    Exemple: {"id":1,"title":"Move a couch","city":"Portland, OR","category":"Moving help","pay":60,"description":"..."}
    """
    # TODO: utilise ta DB
    return None


def save_application(job_id: int, full_name: str, phone: str, email: str, message: str):
    """
    IMPORTANT: remplace le contenu par TA fonction DB qui enregistre l'application.
    """
    # TODO: insert DB
    return True


# ----------------------------
# APPLY (GET) -> montre le formulaire
# ----------------------------
@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_page(request: Request, job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        return templates.TemplateResponse("apply_not_found.html", {"request": request, "job_id": job_id})

    return templates.TemplateResponse("apply.html", {
        "request": request,
        "job": job
    })


# ----------------------------
# APPLY (POST) -> submit -> redirect success
# ----------------------------
@app.post("/apply/{job_id}")
def apply_submit(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(""),
    message: str = Form("")
):
    job = get_job_by_id(job_id)
    if not job:
        return RedirectResponse(url=f"/apply/{job_id}", status_code=303)

    save_application(job_id, full_name, phone, email, message)

    # ✅ SUPER IMPORTANT: 303 pour redirect après POST
    return RedirectResponse(url=f"/apply-success/{job_id}", status_code=303)


# ----------------------------
# APPLY SUCCESS (GET)
# ----------------------------
@app.get("/apply-success/{job_id}", response_class=HTMLResponse)
def apply_success(request: Request, job_id: int):
    job = get_job_by_id(job_id)

    return templates.TemplateResponse("apply_success.html", {
        "request": request,   # ✅ OBLIGATOIRE sinon Internal Server Error
        "job": job            # optionnel (notre template gère si job=None)
    })