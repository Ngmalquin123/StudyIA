"""
StudyIA - Endpoints de temas (CRUD).

Un tema siempre vive dentro de una materia. Por eso cada operacion tiene que
verificar dos cosas: que la materia exista y que sea del usuario. Es la regla
de "solo puedes tocar lo tuyo" aplicada a un nivel mas profundo.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies import (
    get_current_user_id,
    get_db,
    get_subject_de_mi,
    get_topic_de_mi,
)
from app.models import Topic
from app.schemas import TopicCreate, TopicRead, TopicUpdate

router = APIRouter(prefix="/api/topics", tags=["Temas"])


@router.post("", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
def crear_tema(
    datos: TopicCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Crea un tema dentro de una materia.

    Se valida la propiedad de la materia ANTES de insertar. Si se hiciera
    despues, el tema ya estaria guardado y habria que deshacerlo a mano.
    """
    get_subject_de_mi(datos.subject_id, user_id, db)

    tema = Topic(
        subject_id=datos.subject_id,
        nombre=datos.nombre,
        descripcion=datos.descripcion,
    )
    db.add(tema)
    db.commit()
    db.refresh(tema)
    return tema


@router.get("", response_model=list[TopicRead])
def listar_temas(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    subject_id: int | None = Query(
        default=None,
        ge=1,
        description="Si se envia, devuelve solo los temas de esa materia.",
    ),
):
    """
    Lista temas. Con `?subject_id=1` acota a una materia; sin el, devuelve
    todos los del usuario.
    """
    consulta = (
        select(Topic)
        # selectinload carga la materia del tema en la misma consulta.
        # Se usa porque al filtrar por el dueño hay que leer topic.subject.
        .join(Topic.subject)
        .options(selectinload(Topic.subject))
    )

    if subject_id is not None:
        get_subject_de_mi(subject_id, user_id, db)
        consulta = consulta.where(Topic.subject_id == subject_id)
    else:
        consulta = consulta.where(Topic.subject.has(user_id=user_id))

    return db.scalars(consulta.order_by(Topic.nombre)).all()


@router.get("/{topic_id}", response_model=TopicRead)
def obtener_tema(
    topic_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return get_topic_de_mi(topic_id, user_id, db)


@router.patch("/{topic_id}", response_model=TopicRead)
def actualizar_tema(
    topic_id: int,
    datos: TopicUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Actualiza un tema. No se puede cambiar de materia: se crea otro tema."""
    tema = get_topic_de_mi(topic_id, user_id, db)

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(tema, campo, valor)

    db.commit()
    db.refresh(tema)
    return tema


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tema(
    topic_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Elimina un tema. Las preguntas y opciones se van en cascada."""
    tema = get_topic_de_mi(topic_id, user_id, db)
    db.delete(tema)
    db.commit()
