from sqlalchemy.orm import Session
from app.db.models import School


def create_school(db: Session, school: School) -> School:
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def get_school_by_id(db: Session, school_id: int) -> School | None:
    return db.query(School).filter(School.id == school_id).first()
