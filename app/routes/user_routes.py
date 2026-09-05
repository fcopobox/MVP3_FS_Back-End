from fastapi import APIRouter, Depends, HTTPException, Header, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal, Base, engine
from app.models import User
from app.auth.jwt_handler import create_access_token, verify_token
from pydantic import BaseModel, EmailStr
import bcrypt

# criar tabelas
Base.metadata.create_all(bind=engine)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.post("/user/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not bcrypt.checkpw(user.password.encode("utf-8"), db_user.password_hash.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token({"sub": str(db_user.id)})
    return {
        "access_token": token,
         "token_type": "bearer",
         "user": {
             "id": db_user.id,
             "name": db_user.name,
             "email": db_user.email
         }
     }

@router.api_route("/user/register", methods=["POST", "OPTIONS"])
def register(user: UserCreate = None, db: Session = Depends(get_db)):
    if user is None:  # preflight OPTIONS
        return {}

    try:
        hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
        db_user = User(
            name=user.name,
            email=user.email,
            password_hash=hashed_pw.decode("utf-8"),
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        token = create_access_token({"sub": str(db_user.id)})
        return {
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email,
            "access_token": token,
            "token_type": "bearer",
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email já cadastrado")

def get_current_user(token: str = Header(...), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user
class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None

@router.put("/user/{id}")
def update_user(id: int, user_update: UserUpdate, 
                db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user)):
    if current_user.id != id:
        raise HTTPException(status_code=403, detail="Não autorizado")

    # Atualizar apenas campos enviados
    for field, value in user_update.dict(exclude_unset=True).items():
        if field == "email":
            # validar unicidade
            if db.query(User).filter(User.email == value, User.id != id).first():
                raise HTTPException(status_code=400, detail="Email já cadastrado")
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return {"id": current_user.id, "email": current_user.email, "name": current_user.name}

@router.put("/user/{id}/change-password")
def change_password(
    id: int,
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Garantir que o usuário só altera a própria senha
    if current_user.id != id:
        raise HTTPException(status_code=403, detail="Operação não permitida.")

    # Validar senha atual
    if not bcrypt.checkpw(payload.old_password.encode("utf-8"), current_user.password_hash.encode("utf-8")):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")

    # Validar tamanho da nova senha
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="A nova senha deve ter pelo menos 8 caracteres.")

    # Validar se nova senha é diferente da atual
    if bcrypt.checkpw(payload.new_password.encode("utf-8"), current_user.password_hash.encode("utf-8")):
        raise HTTPException(status_code=400, detail="A nova senha deve ser diferente da atual.")

    # Gerar novo hash
    hashed_new_pw = bcrypt.hashpw(payload.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Atualizar no banco
    current_user.password_hash = hashed_new_pw
    db.commit()

    return {"message": "Senha alterada com sucesso"}

@router.delete("/user/{id}")
def delete_user(id: int, 
                db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user)):
    if current_user.id != id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    db.delete(current_user)
    db.commit()
    return {"detail": "Usuário excluído com sucesso"}


@router.get("/user/{id}")
def get_user(id: int, 
             db: Session = Depends(get_db), 
             current_user: User = Depends(get_current_user)):
    if current_user.id != id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
  }

@router.get("/admin/all")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "name": u.name, "email": u.email} for u in users]