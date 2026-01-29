from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from models import Job, Application

def create_job(db: Session, title: str, city: str, category: str, pay: str, description: str) -> Job:
    job = Job(
        title=title.strip(),
        city=city.strip(),
        category=category.strip(),
        pay=(pay or "").strip().replace("$", ""),
        description=description.strip(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_job(db: Session, job_id: int) -> Optional[Job]:
    return db.get(Job, job_id)

def list_jobs(db: Session, q: str = "", city: str = "", category: str = "") -> List[Job]:
    stmt = select(Job)

    if q:
        qv = f"%{q.lower()}%"
        stmt = stmt.where((Job.title.ilike(qv)) | (Job.description.ilike(qv)))
    if city:
        cv = f"%{city.lower()}%"
        stmt = stmt.where(Job.city.ilike(cv))
    if category:
        stmt = stmt.where(Job.category.ilike(category))

    stmt = stmt.order_by(desc(Job.id))
    return list(db.execute(stmt).scalars().all())

def create_application(
    db: Session,
    job_id: int,
    full_name: str,
    phone: str,
    email: Optional[str] = None,
    message: Optional[str] = None,
) -> Application:
    app = Application(
        job_id=job_id,
        full_name=full_name.strip(),
        phone=phone.strip(),
        email=(email or "").strip() or None,
        message=(message or "").strip() or None,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app