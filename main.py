import os
import smtplib
from email.message import EmailMessage

from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import SessionLocal, engine
from models import Base, Job, Application

# Create tables if they don't exist (safe)
Base.metadata.create_all(bind=engine)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")


# -----------------------
# SMTP / EMAIL UTILITIES
# -----------------------
def _get_env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip()

def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Uses SMTP variables (Render Environment Variables):
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL
    """
    smtp_host = _get_env("SMTP_HOST")
    smtp_port = int(_get_env("SMTP_PORT", "587") or "587")
    smtp_user = _get_env("SMTP_USER")
    smtp_pass = _get_env("SMTP_PASS")
    from_email = _get_env("FROM_EMAIL", smtp_user)

    if not (smtp_host and smtp_user and smtp_pass and from_email):
        # Pas d'email configuré => on évite crash, mais on log/flash
        raise RuntimeError("SMTP not configured. Missing SMTP_HOST/SMTP_USER/SMTP_PASS/FROM_EMAIL")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)

    # TLS standard (587)
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


# -----------------------
# DB helper
# -----------------------
def get_db() -> Session:
    return SessionLocal()


# -----------------------
# ROUTES
# -----------------------
@app.route("/")
def home():
    q = (request.args.get("q") or "").strip()
    city = (request.args.get("city") or "").strip()
    category = (request.args.get("category") or "").strip()

    db = get_db()
    try:
        query = db.query(Job)

        if q:
            like = f"%{q}%"
            query = query.filter(or_(Job.title.ilike(like), Job.description.ilike(like), Job.category.ilike(like)))

        if city:
            query = query.filter(Job.city.ilike(f"%{city}%"))

        if category and category.lower() != "all":
            query = query.filter(Job.category.ilike(f"%{category}%"))

        jobs = query.order_by(Job.created_at.desc()).all()
        return render_template("index.html", jobs=jobs, q=q, city=city, category=category)
    finally:
        db.close()


@app.route("/post", methods=["GET"])
def post_job_form():
    return render_template("post_job.html")


@app.route("/post", methods=["POST"])
def post_job_submit():
    title = (request.form.get("title") or "").strip()
    city = (request.form.get("city") or "").strip()
    category = (request.form.get("category") or "").strip()
    pay = (request.form.get("pay") or "").strip()
    description = (request.form.get("description") or "").strip()

    poster_email = (request.form.get("poster_email") or "").strip()
    poster_phone = (request.form.get("poster_phone") or "").strip()

    if not title or not city or not category or not description or not poster_email:
        flash("Please fill required fields (including your email).", "error")
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
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        return redirect(url_for("job_detail", job_id=job.id))
    finally:
        db.close()


@app.route("/jobs/<int:job_id>")
def job_detail(job_id: int):
    db = get_db()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return render_template("404.html"), 404
        return render_template("job_detail.html", job=job)
    finally:
        db.close()


@app.route("/apply/<int:job_id>", methods=["GET"])
def apply_form(job_id: int):
    db = get_db()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return render_template("404.html"), 404
        return render_template("apply_job.html", job=job)
    finally:
        db.close()

@app.route("/apply/<int:job_id>", methods=["POST"])
def apply_submit(job_id: int):
    applicant_name = (request.form.get("applicant_name") or "").strip()
    applicant_email = (request.form.get("applicant_email") or "").strip()
    applicant_phone = (request.form.get("applicant_phone") or "").strip()
    message = (request.form.get("message") or "").strip()

    if not applicant_name or not applicant_email:
        flash("Name and email are required.", "error")
        return redirect(url_for("apply_form", job_id=job_id))

    db = get_db()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            flash("Job not found.", "error")
            return redirect(url_for("jobs"))

        # 1️⃣ Save application
        application = Application(
            job_id=job.id,
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            applicant_phone=applicant_phone or None,
            message=message or None,
        )
        db.add(application)
        db.commit()

        # 2️⃣ Send email to employer (job poster)
        subject = f"New application for your job: {job.title}"
        body = f"""
Hi,

Someone just applied to your job on Win-Win Job.

JOB
• Title: {job.title}
• City: {job.city}
• Category: {job.category}
• Pay: {job.pay or "N/A"}

APPLICANT
• Name: {applicant_name}
• Email: {applicant_email}
• Phone: {applicant_phone or "N/A"}
• Message: {message or "No message"}

You can reply directly to the applicant to connect.

— Win-Win Job
"""

        try:
            send_email(job.poster_email, subject, body)
        except Exception as e:
            print("EMAIL ERROR:", e)

        flash("Your application has been sent successfully!", "success")
        return redirect(url_for("job_detail", job_id=job.id))

    finally:
        db.close()
        

        # ✅ Notify employer (poster)
        try:
            subject = f"New application: {job.title} ({job.city})"
            body = (
                f"Hello,\n\n"
                f"Someone applied to your job on Win-Win Job.\n\n"
                f"JOB\n"
                f"- Title: {job.title}\n"
                f"- City: {job.city}\n"
                f"- Category: {job.category}\n"
                f"- Pay: {job.pay or 'N/A'}\n\n"
                f"APPLICANT\n"
                f"- Name: {applicant_name}\n"
                f"- Email: {applicant_email}\n"
                f"- Phone: {applicant_phone or 'N/A'}\n\n"
                f"Message:\n{message or '(No message)'}\n\n"
                f"Tip: You can reply directly to the applicant by email.\n"
            )
            send_email(job.poster_email, subject, body)
        except Exception as e:
            # On ne bloque pas la candidature si l'email échoue
            print("EMAIL ERROR:", str(e))

        return render_template("apply_success.html", job=job)

    finally:
        db.close()


# Simple pages (optionnel)
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))