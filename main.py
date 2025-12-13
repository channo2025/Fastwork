from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request
import sqlite3

def get_db_jobs():
    conn = sqlite3.connect("fastwork_db.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("SELECT * FROM job ORDER BY id DESC").fetchall()

    conn.close()
    return [dict(r) for r in rows]

app = Flask(__name__)
app.secret_key = "jobdash-secret-key"  # ok pour dev

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fastwork_db.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # pour accéder comme dict: row["title"]
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Table des jobs (tasks)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            city TEXT,
            duration_hours REAL,
            pay INTEGER NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # (Optionnel) table applications - on l'utilisera STEP 3
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    """)

    conn.commit()
    conn.close()


def seed_jobs_if_empty():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM jobs")
    count = cur.fetchone()["c"]

    if count == 0:
        demo = [
            ("Deep clean 1-bedroom", "SE Portland", "Portland", 3, 85, "Deep clean: kitchen + bathroom + floors."),
            ("Move boxes to storage", "Gresham", "Gresham", 2, 60, "Help move 10–15 boxes to a storage unit."),
            ("Yard mowing + cleanup", "NE Portland", "Portland", 2.5, 70, "Mow front yard + bag clippings."),
            ("Grocery shopping + drop-off", "Downtown", "Portland", 1.5, 45, "Pick up groceries and deliver same day.")
        ]
        cur.executemany("""
            INSERT INTO jobs (title, location, city, duration_hours, pay, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, demo)
        conn.commit()

    conn.close()


@app.route("/")
def index():
    # Ta homepage existe déjà: templates/index.html
    return render_template("index.html")


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request):
    tasks = get_db_jobs()
    return templates.TemplateResponse("tasks.html", {"request": request, "tasks": tasks})


@app.route("/post-job", methods=["GET", "POST"])
def post_job():
    # Si tu as déjà un post_job.html, on le garde
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        location = request.form.get("location", "").strip()
        city = request.form.get("city", "").strip()
        duration_hours = request.form.get("duration_hours", "").strip()
        pay = request.form.get("pay", "").strip()
        description = request.form.get("description", "").strip()

        if not title or not location or not pay:
            flash("Please fill: Title, Location, and Pay.")
            return redirect(url_for("post_job"))

        try:
            pay_int = int(pay)
        except:
            flash("Pay must be a number.")
            return redirect(url_for("post_job"))

        dur_val = None
        if duration_hours:
            try:
                dur_val = float(duration_hours)
            except:
                dur_val = None

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jobs (title, location, city, duration_hours, pay, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, location, city, dur_val, pay_int, description))
        conn.commit()
        conn.close()

        flash("Job posted ✅")
        return redirect(url_for("tasks"))

    return render_template("post_job.html")


# pages légales (si elles existent chez toi)
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")


if __name__ == "__main__":
    init_db()
    seed_jobs_if_empty()
    app.run(debug=True)

@app.get("/apply/{job_id}", response_class=HTMLResponse)
def apply_page(request: Request, job_id: int):
    conn = sqlite3.connect("fastwork_db.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    job = cur.execute("SELECT * FROM job WHERE id = ?", (job_id,)).fetchone()
    conn.close()

    if not job:
        return HTMLResponse("Job not found", status_code=404)

    return templates.TemplateResponse("apply.html", {"request": request, "job": dict(job)})