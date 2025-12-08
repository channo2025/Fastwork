from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Templates & static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------------------
# HOME PAGE
# ---------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ---------------------------
# POST A JOB PAGE (GET)
# ---------------------------
@app.get("/post-job", response_class=HTMLResponse)
async def post_job_page(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})


# ---------------------------
# POST A JOB (FORM SUBMISSION)
# ---------------------------
@app.post("/post-job")
async def post_job_submit(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    budget: str = Form(...),
    when: str = Form(...),
    category: str = Form(...)
):
    # For now, we just print it (later we'll save to database)
    print("\n--- NEW JOB RECEIVED ---")
    print("Title:", title)
    print("Description:", description)
    print("Location:", location)
    print("Budget:", budget)
    print("When:", when)
    print("Category:", category)
    print("-------------------------\n")

    # Redirect user back to home after posting
    return RedirectResponse(url="/", status_code=303)