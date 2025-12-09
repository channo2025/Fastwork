from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# STATIC + TEMPLATES
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Liste en mémoire pour stocker les jobs postés
jobs = []


# ---------------------------
# HOME PAGE
# ---------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # On envoie la liste des jobs au template
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jobs": jobs,   # <--- important
        },
    )


# ---------------------------
# GET: POST A JOB (PAGE FORM)
# ---------------------------
@app.get("/post-job", response_class=HTMLResponse)
async def get_post_job(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


# ---------------------------
# POST: SUBMIT JOB
# ---------------------------
@app.post("/post-job", response_class=HTMLResponse)
async def submit_post_job(request: Request):
    form = await request.form()

    # On crée un job à partir du formulaire
    new_job = {
        "title": form.get("title", "").strip(),
        "description": form.get("description", "").strip(),
        "location": form.get("location", "").strip(),
        "budget": form.get("budget", "").strip(),
        "when": form.get("when", "").strip(),
        "task_type": form.get("task_type", "").strip(),
    }

    # On l'ajoute à la liste (en haut de la liste)
    if new_job["title"]:
        jobs.insert(0, new_job)

    print("\n===== NEW JOB POSTED =====")
    for k, v in new_job.items():
        print(f"{k}: {v}")
    print("==========================\n")

    # Page de confirmation
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>Job posted – JobDash</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background: white;
                padding: 30px 40px;
                border-radius: 16px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                text-align: center;
            }
            h1 { margin-bottom: 10px; }
            p { color: #555; margin-bottom: 20px; }
            a {
                display: inline-block;
                padding: 10px 18px;
                border-radius: 999px;
                text-decoration: none;
                background: #2563eb;
                color: white;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Job posted 🎉</h1>
            <p>Your task has been submitted successfully.</p>
            <a href="/">Back to home</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)