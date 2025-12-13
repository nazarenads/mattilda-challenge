from datetime import datetime

from sqlalchemy.orm import Session

from app.auth import get_password_hash, verify_password
from app.db.models import User
from app.schemas import UserCreate, UserUpdate


def create_user(db: Session, user_data: UserCreate) -> User:
    now = datetime.now()
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        school_id=user_data.school_id,
        is_admin=user_data.is_admin,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, offset: int = 0, limit: int = 100) -> list[User]:
    return db.query(User).offset(offset).limit(limit).all()


def get_users_with_count(
    db: Session, offset: int = 0, limit: int = 100
) -> tuple[list[User], int]:
    total = db.query(User).count()
    items = db.query(User).offset(offset).limit(limit).all()
    return items, total


def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            setattr(user, "hashed_password", get_password_hash(value))
        else:
            setattr(user, field, value)
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

