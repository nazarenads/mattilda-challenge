from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import SchoolCreate, SchoolUpdate, SchoolResponse, PaginatedResponse
from app.services.school import (
    get_school_by_id,
    get_schools_with_count,
    create_school,
    update_school,
    delete_school,
)
from app.db.models import School

router = APIRouter(
    prefix="/school",
    tags=["school"],
)


@router.get("/", response_model=PaginatedResponse[SchoolResponse])
def list_schools(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    """Returns a paginated list of schools."""
    items, total = get_schools_with_count(db, offset=offset, limit=limit)
    pages = (total + limit - 1) // limit if limit > 0 else 0
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset, pages=pages)


@router.get("/{school_id}", response_model=SchoolResponse)
def get_school(school_id: int, db: Session = Depends(get_db)):
    """Returns the school details."""
    school = get_school_by_id(db, school_id)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return school


@router.post("/", response_model=SchoolResponse, status_code=201)
def post_school(school_data: SchoolCreate, db: Session = Depends(get_db)):
    """Creates a new school."""
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
def put_school(
    school_id: int, school_data: SchoolUpdate, db: Session = Depends(get_db)
):
    """Updates an existing school."""
    school = get_school_by_id(db, school_id)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    school.updated_at = datetime.now()
    return update_school(db, school, school_data)


@router.delete("/{school_id}", status_code=204)
def delete_school(school_id: int, db: Session = Depends(get_db)):
    """Deletes a school."""
    school = get_school_by_id(db, school_id)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    delete_school(db, school)
