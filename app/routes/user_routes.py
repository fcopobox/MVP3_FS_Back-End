from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
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
    street: str
    number: str
    complement: str | None = None
    district: str
    city: str
    state: str
    zip_code: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=hashed_pw.decode("utf-8"),
        street=user.street,
        number=user.number,
        complement=user.complement,
        district=user.district,
        city=user.city,
        state=user.state,
        zip_code=user.zip_code
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "email": db_user.email}


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not bcrypt.checkpw(user.password.encode("utf-8"), db_user.password_hash.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(token: str = Header(...), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    street: str | None = None
    number: str | None = None
    complement: str | None = None
    district: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None


@router.put("/{id}")
def update_user(id: int, user_update: UserUpdate, 
                db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user)):
    if current_user.id != id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Atualizar apenas campos enviados
    for field, value in user_update.dict(exclude_unset=True).items():
        if field == "email":
            # validar unicidade
            if db.query(User).filter(User.email == value, User.id != id).first():
                raise HTTPException(status_code=400, detail="Email already in use")
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return {"id": current_user.id, "email": current_user.email, "name": current_user.name}


@router.delete("/{id}")
def delete_user(id: int, 
                db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user)):
    if current_user.id != id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(current_user)
    db.commit()
    return {"detail": "User deleted successfully"}


@router.get("/{id}")
def get_user(id: int, 
             db: Session = Depends(get_db), 
             current_user: User = Depends(get_current_user)):
    if current_user.id != id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "street": current_user.street,
        "number": current_user.number,
        "complement": current_user.complement,
        "district": current_user.district,
        "city": current_user.city,
        "state": current_user.state,
        "zip_code": current_user.zip_code
    }

@router.get("/admin/all")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "name": u.name, "email": u.email} for u in users]



