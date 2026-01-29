import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, Job, Application

# --------------------
# App config
# --------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# Create tables (safe)
Base.metadata.create_all(bind=engine)

# --------------------
# Helpers
# --------------------
def get_db():
    return SessionLocal()

def send_email(to_email, subject, body):
    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASS = os.environ.get("SMTP_PASS")
    FROM_EMAIL = os.environ.get("FROM_EMAIL")

    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS, FROM_EMAIL]):
        print("⚠️ SMTP not configured, email skipped")
        return

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

# --------------------
# Routes
# --------------------

@app.route("/")
def home():
    return redirect(url_for("list_jobs"))

@app.route("/jobs")
def list_jobs():
    db = get_db()
    try:
        jobs = db.query(Job).order_by(Job.id.desc()).all()
        return render_template("jobs.html", jobs=jobs)
    finally:
        db.close()

# --------------------
# POST A JOB
# --------------------
@app.route("/post", methods=["GET"])
def post_job_form():
    return render_template("post_job.html")

@app.route("/post", methods=["POST"])
def post_job_submit():
    title = request.form.get("title", "").strip()
    city = request.form.get("city", "").strip()
    category = request.form.get("category", "").strip()
    pay = (request.form.get("pay") or "").strip()
    description = request.form.get("description", "").strip()
    poster_email = request.form.get("poster_email", "").strip()
    poster_phone = (request.form.get("poster_phone") or "").strip()

    if not title or not city or not category or not description or not poster_email:
        flash("Please fill all required fields (including email).", "error")
        return redirect(url_for("post_job_form"))

    db = get_db()
    try:
        job = Job(
            title=title,
            city=city,
            category=category,
            pay=pay if pay else None,
            description=description,
            poster_email=poster_email,
            poster_phone=poster_phone if poster_phone else None,
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        flash("Job published successfully!", "success")
        return redirect(url_for("list_jobs"))
    except Exception as e:
        db.rollback()
        print("POST JOB ERROR:", e)
        flash("Something went wrong.", "error")
        return redirect(url_for("post_job_form"))
    finally:
        db.close()

# --------------------
# APPLY TO JOB
# --------------------
@app.route("/apply/<int:job_id>", methods=["GET"])
def apply_form(job_id):
    db = get_db()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return render_template("404.html"), 404
        return render_template("apply_job.html", job=job)
    finally:
        db.close()

@app.route("/apply/<int:job_id>", methods=["POST"])
def apply_submit(job_id):
    applicant_name = request.form.get("applicant_name", "").strip()
    applicant_email = request.form.get("applicant_email", "").strip()
    applicant_phone = (request.form.get("applicant_phone") or "").strip()
    message = (request.form.get("message") or "").strip()

    if not applicant_name or not applicant_email:
        flash("Name and email are required.", "error")
        return redirect(url_for("apply_form", job_id=job_id))

    db = get_db()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return render_template("404.html"), 404

        application = Application(
            job_id=job.id,
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            applicant_phone=applicant_phone if applicant_phone else None,
            message=message,
            created_at=datetime.utcnow()
        )
        db.add(application)
        db.commit()

        # Email employer
        email_body = f"""
New applicant for your job: {job.title}

Name: {applicant_name}
Email: {applicant_email}
Phone: {applicant_phone}

Message:
{message}
"""
        send_email(
            job.poster_email,
            f"New applicant for: {job.title}",
            email_body
        )

        flash("Application sent successfully!", "success")
        return redirect(url_for("list_jobs"))

    except Exception as e:
        db.rollback()
        print("APPLY ERROR:", e)
        flash("Something went wrong.", "error")
        return redirect(url_for("apply_form", job_id=job_id))
    finally:
        db.close()

# --------------------
# Run
# --------------------
if __name__ == "__main__":
    app.run(debug=True)