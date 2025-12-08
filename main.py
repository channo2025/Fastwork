from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
app = FastAPI()

@app.get("/post-job", response_class=HTMLResponse)
async def get_post_job(request: Request):
    return templates.TemplateResponse("post_job.html", {"request": request})

@app.post("/post-job")
async def submit_job(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    budget: float = Form(...),
    when: str = Form(...),
    task_type: str = Form(...)
):
    print("New job posted:")
    print(title, description, location, budget, when, task_type)

    # Redirect after success
    return RedirectResponse(url="/", status_code=303)