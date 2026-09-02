from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import User
from app.auth.verify_token import verify_token

router = APIRouter(prefix="/user", tags=["user"])


# -----------------------------
# Pydantic Schemas
# -----------------------------
class UserCreate(BaseModel):
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
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    auth0_id = token_payload["sub"]
    email = token_payload["email"]

    existing = db.query(User).filter(User.auth0_id == auth0_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuário já existe no sistema")

    db_user = User(
        auth0_id=auth0_id,
        email=email,
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
# GET - Buscar usuário do próprio Auth0
# -----------------------------
@router.get("/me", dependencies=[Depends(verify_token)])
def get_my_user(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    auth0_id = token_payload["sub"]

    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return user


# -----------------------------
# PUT - Atualizar usuário
# -----------------------------
@router.put("/me", dependencies=[Depends(verify_token)])
def update_my_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    auth0_id = token_payload["sub"]

    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = user_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user


# -----------------------------
# PUT - Atualizar email (Auth0 + Banco)
# -----------------------------
from app.auth0_management import update_auth0_email

class EmailUpdate(BaseModel):
    email: str

@router.put("/me/email", dependencies=[Depends(verify_token)])
def update_my_email(
    data: EmailUpdate,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    auth0_id = token_payload["sub"]

    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Atualiza no Auth0
    update_auth0_email(auth0_id, data.email)

    # Atualiza no banco
    user.email = data.email
    db.commit()
    db.refresh(user)

    return {"message": "Email atualizado com sucesso"}


# -----------------------------
# POST - Reset de senha via Auth0
# -----------------------------
from app.auth0_management import send_password_reset

@router.post("/me/reset-password", dependencies=[Depends(verify_token)])
def reset_password(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    email = token_payload["email"]

    send_password_reset(email)

    return {"message": "Email de redefinição enviado"}
    

# -----------------------------
# DELETE - Remover usuário
# -----------------------------
from app.auth0_management import delete_auth0_user

@router.delete("/me", dependencies=[Depends(verify_token)])
def delete_my_user(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token)
):
    auth0_id = token_payload["sub"]

    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    db.delete(user)
    db.commit()

    delete_auth0_user(auth0_id)

    return {"message": "Usuário removido com sucesso"}
