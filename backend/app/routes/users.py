from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    """Payload d'entree du POST /users (demo)."""

    username: str = Field(min_length=2, max_length=50)
    preferred_language: str = Field(default="fr", max_length=5)


class UserOut(BaseModel):
    """Representation JSON renvoyee par les routes (demo)."""

    id: UUID
    username: str
    preferred_language: str
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Insere un utilisateur dans la table Neon 'users'."""
    existing = db.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Le username '{payload.username}' existe deja.",
        )

    user = User(
        username=payload.username,
        preferred_language=payload.preferred_language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    """Liste tous les utilisateurs (limite a 50 pour la demo)."""
    users = db.execute(
        select(User).order_by(User.created_at.desc()).limit(50)
    ).scalars().all()
    return users


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Recupere un utilisateur par son UUID."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return user
