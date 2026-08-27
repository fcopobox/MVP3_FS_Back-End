from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import verify_token
from pydantic import BaseModel

from fastapi import Depends
from app.auth.verify_token import verify_token

router = APIRouter(prefix="/user", tags=["user"])


# -----------------------------
# Pydantic Schemas
# -----------------------------
class UserCreate(BaseModel):
    email: str
    name: str
    cep: str | None = None
    address: str | None = None
    number: str | None = None
    complement: str | None = None
    district: str | None = None
    city: str | None = None
    state: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    cep: str | None = None
    address: str | None = None
    number: str | None = None
    complement: str | None = None
    district: str | None = None
    city: str | None = None
    state: str | None = None


# -----------------------------
# POST - Criar usuário
# -----------------------------
@router.post("/", dependencies=[Depends(verify_token)])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        email=user.email,
        name=user.name,
        cep=user.cep,
        address=user.address,
        number=user.number,
        complement=user.complement,
        district=user.district,
        city=user.city,
        state=user.state
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


# -----------------------------
# GET - Buscar usuário por ID
# -----------------------------
@router.get("/{user_id}", dependencies=[Depends(verify_token)])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return user


# -----------------------------
# PUT - Atualizar usuário
# -----------------------------
@router.put("/{user_id}", dependencies=[Depends(verify_token)])
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = user_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user


# -----------------------------
# DELETE - Remover usuário
# -----------------------------
@router.delete("/{user_id}", dependencies=[Depends(verify_token)])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    db.delete(user)
    db.commit()

    return {"message": "Usuário removido com sucesso"}
