from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from studyia.api.routes import auth, roles, users
from studyia.core.config import settings
from studyia.database.connection import test_connection


app = FastAPI(
    title="StudyIA API",
    description="API backend para la plataforma StudyIA",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(roles.router, prefix="/api")


@app.get("/health", tags=["Salud"])
def health_check():
    try:
        database = "ok" if test_connection() else "error"
    except Exception:
        database = "error"

    return {
        "status": "ok",
        "service": settings.app_name,
        "database": database,
    }
