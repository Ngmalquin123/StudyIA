"""
StudyIA - Punto de entrada del backend.

Este archivo es el que arranca todo. Su trabajo es pequeno y deliberado:

  1. Crear la aplicacion de FastAPI.
  2. Activar CORS (para que el frontend Angular pueda llamar a la API).
  3. Incluir los routers.

Por eso el resto del codigo vive en `app/` y no aqui. Si todo estuviera en
main.py, en dos semanas seria un archivo de 2000 lineas imposible de navegar.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import questions, subjects, topics

# metadata aparece en /docs. Son los datos que el equipo ve al abrir Swagger.
app = FastAPI(
    title="StudyIA API",
    description=(
        "API de StudyIA: materias, temas y preguntas de opcion multiple.\n\n"
        "**Temporal:** la identidad del usuario se envia en la cabecera "
        "`X-User-Id`. Se reemplaza por JWT en la Fase 4."
    ),
    version="0.3.0",
)

# --- CORS -------------------------------------------------------------------
# Que es: por seguridad, un navegador solo deja que una pagina de otra
# dominio llame a una API si el servidor lo autoriza explicitamente.
#
# Sin esto, al llamar http://localhost:8000 desde http://localhost:4200 el
# navegador bloquearia la peticion con un error de CORS. Opciones y credenciales.
origins = settings.cors_origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ----------------------------------------------------------------
# Cada router agrupa los endpoints de una entidad. Sus URLs empiezan por el
# prefijo que se defino en el router: /api/subjects, /api/topics, /api/questions.
app.include_router(subjects.router)
app.include_router(topics.router)
app.include_router(questions.router)


# --- Salud ------------------------------------------------------------------
@app.get("/", tags=["Salud"])
def inicio():
    """Endpoint de comprobacion: confirma que el servidor esta vivo."""
    return {
        "mensaje": "Mi API funciona correctamente",
        "version": "0.3.0",
        "docs": "/docs",
    }


@app.get("/api/salud", tags=["Salud"])
def salud():
    """Comprueba tambien que la base de datos responde."""
    from sqlalchemy import text

    from app.database import engine

    try:
        with engine.connect() as conexion:
            conexion.execute(text("SELECT 1"))
        base_datos = "conectada"
    except Exception:
        base_datos = "sin conexion"

    return {
        "estado": "ok",
        "base_de_datos": base_datos,
        "proveedor_ia": settings.IA_PROVEEDOR,
    }
