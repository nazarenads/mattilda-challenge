from sqlalchemy.orm import Session
from app.db.models import Student
from app.schemas import StudentUpdate


def create_student(db: Session, student: Student) -> Student:
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_student_by_id(db: Session, student_id: int) -> Student | None:
    return db.query(Student).filter(Student.id == student_id).first()


def get_students(db: Session, offset: int = 0, limit: int = 100) -> list[Student]:
    return db.query(Student).offset(offset).limit(limit).all()


def get_students_with_count(
    db: Session, offset: int = 0, limit: int = 100
) -> tuple[list[Student], int]:
    total = db.query(Student).count()
    items = db.query(Student).offset(offset).limit(limit).all()
    return items, total


def update_student(db: Session, student: Student, student_data: StudentUpdate) -> Student:
    update_data = student_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student: Student) -> None:
    db.delete(student)
    db.commit()
