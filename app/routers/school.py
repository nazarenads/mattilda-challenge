from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import School, User
from app.dependencies import get_db, get_current_active_user, require_admin
from app.schemas import SchoolCreate, SchoolUpdate, SchoolResponse, PaginatedResponse, BalanceResponse
from app.services import school as school_service

router = APIRouter(
    prefix="/school",
    tags=["school"],
)


@router.get("/", response_model=PaginatedResponse[SchoolResponse])
def list_schools(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Returns a paginated list of schools (admin only)."""
    items, total = school_service.get_schools_with_count(db, offset=offset, limit=limit)
    pages = (total + limit - 1) // limit if limit > 0 else 0
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset, pages=pages)


@router.get("/{school_id}", response_model=SchoolResponse)
def get_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns the school details."""
    school = school_service.get_school_by_id_for_user(db, school_id, current_user)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return school


@router.get("/{school_id}/balance", response_model=BalanceResponse)
def get_school_balance(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns the balance summary for a school."""
    school = school_service.get_school_by_id_for_user(db, school_id, current_user)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return school_service.get_school_balance(db, school_id)


@router.post("/", response_model=SchoolResponse, status_code=201)
def create_school(
    school_data: SchoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Creates a new school (admin only)."""
    now = datetime.now()
    school = School(
        name=school_data.name,
        country=school_data.country,
        tax_id=school_data.tax_id,
        created_at=now,
        updated_at=now,
    )
    return school_service.create_school(db, school)


@router.put("/{school_id}", response_model=SchoolResponse)
def update_school(
    school_id: int,
    school_data: SchoolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Updates an existing school (admin only)."""
    school = school_service.get_school_by_id(db, school_id)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    school.updated_at = datetime.now()
    return school_service.update_school(db, school, school_data)


@router.delete("/{school_id}", status_code=204)
def delete_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Deletes a school (admin only)."""
    school = school_service.get_school_by_id(db, school_id)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    school_service.delete_school(db, school)
