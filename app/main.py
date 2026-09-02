from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer
from app.routes.health_routes import router as health_router
from app.routes.user_routes import router as user_router
from app.database import Base, engine
from app.auth.verify_token import verify_token

app = FastAPI()

# Inicializa o banco
Base.metadata.create_all(bind=engine)

security = HTTPBearer()

@app.get("/auth-test")
def auth_test(token = Depends(security)):
    payload = verify_token(token.credentials)
    return {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "message": "Token válido. Backend + Auth0 funcionando!"
    }

app.include_router(health_router)
app.include_router(user_router)
