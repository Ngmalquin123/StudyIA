"""
StudyIA - Dependencias compartidas de la API.

Una "dependencia" en FastAPI es una función que se ejecuta ANTES del endpoint
y le entrega algo. Se declara con `Depends(...)`.

Sirve para dos cosas:
  1. No repetir codigo en cada endpoint (conectar a la BD, saber quien llama).
  2. Centralizar las reglas de seguridad en un solo lugar.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db

# Reexportamos get_db para que los routers hagan un solo import.
__all__ = ["get_db", "get_current_user_id", "get_subject_de_mi", "get_topic_de_mi"]


def get_current_user_id(
    x_user_id: int = Header(
        ...,
        alias="X-User-Id",
        description="ID del usuario. TEMPORAL: se reemplaza por el token JWT en la Fase 4.",
    ),
) -> int:
    """
    Devuelve el ID del usuario que esta haciendo la peticion.

    ===================================================================
    ESTO ES PROVISIONAL Y ES UNA FUGA DE SEGURIDAD DELIBERADA.
    ===================================================================
    Cualquiera puede mandar la cabecera `X-User-Id: 5` y hacerse pasar por el
    usuario 5. Sirve unicamente para poder desarrollar y probar el CRUD antes
    de tener el login.

    En la FASE 4 esta funcion entera se reemplaza por una que lea el token
    JWT. El resto del codigo no cambia, porque todos los endpoints piden
    "el usuario actual" y nunca saben de donde sale.
    """
    if x_user_id < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID de usuario debe ser un numero positivo.",
        )
    return x_user_id


# =============================================================================
# AYUDAS DE PROPIEDAD
# =============================================================================
# Estas dos funciones encapsulan la regla mas importante del proyecto:
# "solo puedes tocar lo tuyo".
#
# Reciben el ID de un recurso y el del usuario. Si no coinciden, la respuesta
# es 404 y no 403. A proposito: un 403 confirmaria que ese recurso existe
# ("esa materia existe pero es de otro"). Un 404 no revela nada.


def get_subject_de_mi(subject_id: int, user_id: int, db: Session):
    """Devuelve la materia, pero solo si pertenece al usuario. Si no, 404."""
    from app.models import Subject  # import local: evita imports circulares

    subject = db.get(Subject, subject_id)
    if subject is None or subject.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Materia no encontrada.",
        )
    return subject


def get_topic_de_mi(topic_id: int, user_id: int, db: Session):
    """Devuelve el tema, pero solo si el usuario es dueño de su materia."""
    from app.models import Topic

    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tema no encontrado.",
        )

    # Hay que subir un nivel: el tema no tiene user_id, lo tiene su materia.
    if topic.subject.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tema no encontrado.",
        )
    return topic
