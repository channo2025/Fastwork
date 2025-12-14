from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3

# ... ton code existant ...

def get_db():
    conn = sqlite3.connect("jobs.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_page(request: Request, job_id: int):
    conn = get_db()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()

    if job is None:
        return templates.TemplateResponse("apply_not_found.html", {"request": request})

    return templates.TemplateResponse("apply.html", {"request": request, "job": dict(job)})


@app.post("/apply/{job_id}")
async def apply_submit(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    phone: str = Form(""),
    email: str = Form(...),
    message: str = Form("")
):
    # Vérifie que le job existe
    conn = get_db()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job is None:
        conn.close()
        return RedirectResponse(url="/tasks", status_code=303)

    # Crée la table applications si elle n'existe pas
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            full_name TEXT,
            phone TEXT,
            email TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        INSERT INTO applications (job_id, full_name, phone, email, message)
        VALUES (?, ?, ?, ?, ?)
    """, (job_id, full_name, phone, email, message))

    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/apply-success/{job_id}", status_code=303)


@app.get("/apply-success/{job_id}", response_class=HTMLResponse)
async def apply_success(request: Request, job_id: int):
    return templates.TemplateResponse("apply_success.html", {"request": request, "job_id": job_id})