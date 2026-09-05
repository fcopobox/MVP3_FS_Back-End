from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import user_routes

app = FastAPI(title="WeatherMap Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],  # libera localhost e 127.0.0.1
    allow_origins=["*"],  # libera todos os domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_routes.router)


