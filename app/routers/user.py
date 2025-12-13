import math

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.dependencies import get_db, get_current_active_user, require_admin
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    PaginatedResponse,
)
from app.services import user as user_service
from app.services import school as school_service

router = APIRouter(prefix="/user", tags=["users"])


@router.get("/", response_model=PaginatedResponse[UserResponse])
def list_users(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all users (admin only)."""
    items, total = user_service.get_users_with_count(db, offset=offset, limit=limit)
    pages = math.ceil(total / limit) if limit > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        pages=pages,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get a user by ID (admin only)."""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new user (admin only)."""
    existing_user = user_service.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    if user_data.school_id:
        school = school_service.get_school_by_id(db, user_data.school_id)
        if not school:
            raise HTTPException(status_code=404, detail="School not found")

    return user_service.create_user(db, user_data)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a user (admin only)."""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_data.email:
        existing_user = user_service.get_user_by_email(db, user_data.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered")

    if user_data.school_id:
        school = school_service.get_school_by_id(db, user_data.school_id)
        if not school:
            raise HTTPException(status_code=404, detail="School not found")

    return user_service.update_user(db, user, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a user (admin only)."""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_service.delete_user(db, user)

