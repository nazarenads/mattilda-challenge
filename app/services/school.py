from sqlalchemy.orm import Session
from app.db.models import School
from app.schemas import SchoolUpdate


def create_school(db: Session, school: School) -> School:
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def get_school_by_id(db: Session, school_id: int) -> School | None:
    return db.query(School).filter(School.id == school_id).first()


def get_schools(db: Session, skip: int = 0, limit: int = 100) -> list[School]:
    return db.query(School).offset(skip).limit(limit).all()


def update_school(db: Session, school: School, school_data: SchoolUpdate) -> School:
    update_data = school_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(school, field, value)
    db.commit()
    db.refresh(school)
    return school


def delete_school(db: Session, school: School) -> None:
    db.delete(school)
    db.commit()
