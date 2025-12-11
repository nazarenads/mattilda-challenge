from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import SchoolCreate, SchoolResponse
from app.services.school import get_school_by_id, create_school
from app.db.models import School

router = APIRouter(
    prefix="/school",
    tags=["school"],
)


@router.get("/{school_id}", response_model=SchoolResponse)
def get_school(school_id: int, db: Session = Depends(get_db)):
    """
    Get school endpoint.
    Returns the school details.
    """
    school = get_school_by_id(db, school_id)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return school


@router.post("/", response_model=SchoolResponse, status_code=201)
def create_school_endpoint(school_data: SchoolCreate, db: Session = Depends(get_db)):
    """
    Create school endpoint.
    Creates a new school.
    """
    now = datetime.now()
    school = School(
        name=school_data.name,
        created_at=now,
        updated_at=now,
    )
    return create_school(db, school)
