from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import SchoolCreate, SchoolUpdate, SchoolResponse
from app.services.school import (
    get_school_by_id,
    get_schools,
    create_school,
    update_school,
    delete_school,
)
from app.db.models import School

router = APIRouter(
    prefix="/school",
    tags=["school"],
)


@router.get("/", response_model=list[SchoolResponse])
def list_schools(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List schools endpoint.
    Returns a list of all schools.
    """
    return get_schools(db, skip=skip, limit=limit)


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
        country=school_data.country,
        tax_id=school_data.tax_id,
        created_at=now,
        updated_at=now,
    )
    return create_school(db, school)


@router.put("/{school_id}", response_model=SchoolResponse)
def update_school_endpoint(
    school_id: int, school_data: SchoolUpdate, db: Session = Depends(get_db)
):
    """
    Update school endpoint.
    Updates an existing school.
    """
    school = get_school_by_id(db, school_id)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    school.updated_at = datetime.now()
    return update_school(db, school, school_data)


@router.delete("/{school_id}", status_code=204)
def delete_school_endpoint(school_id: int, db: Session = Depends(get_db)):
    """
    Delete school endpoint.
    Deletes a school.
    """
    school = get_school_by_id(db, school_id)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    delete_school(db, school)
