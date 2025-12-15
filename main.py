from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER

app = FastAPI()

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Exemple data (si tu as déjà jobs, garde le tien) ---
jobs = [
    {"id": 1, "title": "House cleaning", "location": "Portland", "time": "3 hrs", "pay": "$85", "description": "Clean a 1-bedroom apartment.", "contact_email": "example@gmail.com"},
]


@app.post("/apply/{job_id}")
def submit_application(
    request: Request,
    job_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        return HTMLResponse("Job not found", status_code=404)

    # ✅ Pour l’instant: on log (plus tard on envoie email ou on sauvegarde)
    print("NEW APPLICATION:", {"job_id": job_id, "name": full_name, "email": email, "message": message})

    # ✅ Redirige vers une page merci
    return RedirectResponse(url=f"/thank-you?job_id={job_id}", status_code=HTTP_303_SEE_OTHER)
@app.get("/thank-you", response_class=HTMLResponse)
def thank_you(request: Request, job_id: int | None = None):
    return templates.TemplateResponse("thank_you.html", {"request": request, "job_id": job_id})