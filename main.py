from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# templates + static
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------------------
# HOME PAGE
# ---------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ---------------------------
# POST A JOB (PAGE FORMULAIRE)
# ---------------------------
@app.get("/post-job", response_class=HTMLResponse)
async def get_post_job(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


# ---------------------------
# POST A JOB (RÉCEPTION FORMULAIRE)
# ---------------------------
@app.post("/post-job")
async def submit_post_job(request: Request):
    # On récupère TOUT ce que le formulaire envoie
    form = await request.form()

    # Juste pour vérifier dans les logs (Render)
    print("\n------ NEW JOB POSTED ------")
    for key, value in form.items():
        print(f"{key}: {value}")
    print("-----------------------------\n")

    # Pour le moment : on renvoie l'utilisateur sur la home
    return RedirectResponse(url="/", status_code=303)