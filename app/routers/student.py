from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Student, User
from app.dependencies import get_db, get_current_active_user, check_school_access
from app.schemas import StudentCreate, StudentUpdate, StudentResponse, PaginatedResponse, BalanceResponse
from app.services import student as student_service
from app.services import school as school_service

router = APIRouter(
    prefix="/student",
    tags=["student"],
)


@router.get("/", response_model=PaginatedResponse[StudentResponse])
def list_students(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns a paginated list of students."""
    if current_user.is_admin:
        items, total = student_service.get_students_with_count(db, offset=offset, limit=limit)
    else:
        items, total = student_service.get_students_by_school_with_count(
            db, current_user.school_id, offset=offset, limit=limit
        )
    pages = (total + limit - 1) // limit if limit > 0 else 0
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset, pages=pages)


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns the student details."""
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    check_school_access(current_user, student.school_id)
    return student


@router.get("/{student_id}/balance", response_model=BalanceResponse)
def get_student_balance(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns the balance summary for a student."""
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    check_school_access(current_user, student.school_id)
    return student_service.get_student_balance(db, student_id)


@router.post("/", response_model=StudentResponse, status_code=201)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Creates a new student."""
    school = school_service.get_school_by_id(db, student_data.school_id)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    check_school_access(current_user, student_data.school_id)

    now = datetime.now()
    student = Student(
        identifier=student_data.identifier,
        name=student_data.name,
        email=student_data.email,
        school_id=student_data.school_id,
        created_at=now,
        updated_at=now,
    )
    return student_service.create_student(db, student)


@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Updates an existing student."""
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    check_school_access(current_user, student.school_id)

    if student_data.school_id is not None:
        school = school_service.get_school_by_id(db, student_data.school_id)
        if school is None:
            raise HTTPException(status_code=404, detail="School not found")
        check_school_access(current_user, student_data.school_id)

    student.updated_at = datetime.now()
    return student_service.update_student(db, student, student_data)


@router.delete("/{student_id}", status_code=204)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deletes a student."""
    student = student_service.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    check_school_access(current_user, student.school_id)
    student_service.delete_student(db, student)
