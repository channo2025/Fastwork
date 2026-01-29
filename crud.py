from sqlalchemy.orm import Session
from sqlalchemy import or_

from models import Job, Application


def create_job(
    db: Session,
    title: str,
    city: str,
    category: str,
    pay: str | None,
    description: str,
    poster_email: str,
    poster_phone: str | None
) -> Job:
    job = Job(
        title=title.strip(),
        city=city.strip(),
        category=category.strip(),
        pay=(pay.strip() if pay else None),
        description=description.strip(),
        poster_email=poster_email.strip().lower(),
        poster_phone=(poster_phone.strip() if poster_phone else None),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def search_jobs(db: Session, q: str | None, city: str | None, category: str | None) -> list[Job]:
    query = db.query(Job)

    if q:
        q = q.strip()
        query = query.filter(
            or_(
                Job.title.ilike(f"%{q}%"),
                Job.description.ilike(f"%{q}%"),
                Job.category.ilike(f"%{q}%"),
            )
        )

    if city:
        city = city.strip()
        query = query.filter(Job.city.ilike(f"%{city}%"))

    if category and category != "All categories":
        category = category.strip()
        query = query.filter(Job.category == category)

    return query.order_by(Job.created_at.desc()).all()


def get_job(db: Session, job_id: int) -> Job | None:
    return db.query(Job).filter(Job.id == job_id).first()


def create_application(
    db: Session,
    job_id: int,
    applicant_name: str,
    applicant_email: str,
    applicant_phone: str | None,
    message: str | None
) -> Application:
    app = Application(
        job_id=job_id,
        applicant_name=applicant_name.strip(),
        applicant_email=applicant_email.strip().lower(),
        applicant_phone=(applicant_phone.strip() if applicant_phone else None),
        message=(message.strip() if message else None),
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def list_applications_for_job(db: Session, job_id: int) -> list[Application]:
    return db.query(Application).filter(Application.job_id == job_id).order_by(Application.created_at.desc()).all()