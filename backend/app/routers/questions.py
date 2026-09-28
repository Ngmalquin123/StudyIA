"""
StudyIA - Endpoints de preguntas (CRUD) y sus opciones.

Este archivo tiene la logica mas delicada del CRUD por dos motivos:

  1. Las opciones se guardan junto con la pregunta, en la misma peticion.
  2. Un mismo endpoint NO puede devolver la misma informacion que otro:
     listar es para practicar (sin respuestas), ver el detalle es para
     editar (con respuestas). Mezclarlos seria un filtro de examenes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.dependencies import get_current_user_id, get_db, get_topic_de_mi
from app.models import Option, Question
from app.schemas import (
    OptionInput,
    QuestionCreate,
    QuestionDetail,
    QuestionRead,
    QuestionUpdate,
)

router = APIRouter(prefix="/api/questions", tags=["Preguntas"])

# Cargar opciones siempre en la misma consulta evita el problema clasico de
# SQLAlchemy llamado "N+1": si no, al listar 20 preguntas haria 21 consultas
# a la base (1 para las preguntas + 20 para sus opciones).
_OPCIONES = selectinload(Question.options)


def _construir_opciones(datos: list[OptionInput]) -> list[Option]:
    """
    Convierte la lista del cliente en objetos Option.

    Si el cliente no manda `orden`, se asigna la posicion (1, 2, 3...). Asi el
    frontend no tiene que numerar a mano y las opciones siempre salen
    ordenadas.

    OJO con el nombre: el modelo se llama `Option` y su relacion en
    `Question` se llama `options` (en ingles, como la tabla), pero por la API
    el campo se llama `opciones` (en español, como todo lo demas). Son dos
    nombres distintos a proposito: la base y sus tablas van en ingles, la API
    habla español. Hay queTraducirlos al pasar de uno a otro.
    """
    return [
        Option(
            texto=opcion.texto,
            es_correcta=opcion.es_correcta,
            orden=opcion.orden if opcion.orden is not None else posicion,
        )
        for posicion, opcion in enumerate(datos, start=1)
    ]


# =============================================================================
# CREATE
# =============================================================================
@router.post("", response_model=QuestionDetail, status_code=status.HTTP_201_CREATED)
def crear_pregunta(
    datos: QuestionCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Crea una pregunta con sus opciones en una sola llamada.

    Aqui se ve el indice unico parcial en accion: la base garantiza que solo
    haya una opcion correcta. Y el esquema Pydantic garantiza que haya
    exactamente una. Son dos capas distintas defendiendo lo mismo.
    """
    get_topic_de_mi(datos.topic_id, user_id, db)

    pregunta = Question(
        topic_id=datos.topic_id,
        enunciado=datos.enunciado,
        dificultad=datos.dificultad,
        origen=datos.origen,
    )
    # La relacion en el modelo se llama `options`. Se asigna despues de crear
    # el objeto y no en el constructor.
    pregunta.options = _construir_opciones(datos.opciones)

    db.add(pregunta)
    db.commit()
    db.refresh(pregunta)
    return pregunta


# =============================================================================
# READ
# =============================================================================
@router.get("", response_model=list[QuestionRead])
def listar_preguntas(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    topic_id: int = Query(..., ge=1, description="Tema del que se quieren las preguntas"),
):
    """
    Lista las preguntas de un tema PARA PRACTICAR.

    ========================  AVISO DE SEGURIDAD  ==========================
    Este endpoint devuelve `QuestionRead`, que NO incluye `es_correcta`.
    El estudiante no puede ver cual es la respuesta correcta ni aunque
    abra las herramientas de desarrollo del navegador: el campo no viaja en
    la respuesta, no es que este oculto.

    En la Fase 6 el backend corregira las respuestas; el navegador nunca
    decide si el estudiante acerto.
    =======================================================================
    """
    get_topic_de_mi(topic_id, user_id, db)

    consulta = select(Question).where(Question.topic_id == topic_id).options(_OPCIONES)
    return db.scalars(consulta.order_by(Question.id)).all()


@router.get("/{question_id}", response_model=QuestionDetail)
def obtener_pregunta(
    question_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Devuelve la pregunta CON las respuestas correctas.

    Este endpoint es para el formulario de edicion del estudiante, donde si
    necesita ver cual era la opcion correcta. Por eso devuelve
    `QuestionDetail` y no `QuestionRead`.
    """
    pregunta = db.get(Question, question_id, options=[_OPCIONES])
    if pregunta is None or pregunta.topic.subject.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada.",
        )
    return pregunta


# =============================================================================
# UPDATE
# =============================================================================
@router.patch("/{question_id}", response_model=QuestionDetail)
def actualizar_pregunta(
    question_id: int,
    datos: QuestionUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Actualiza una pregunta. Si viene la lista de opciones, se reemplaza
    completa (no se agregan opciones sueltas: habria que decidir cual se
    quita).
    """
    pregunta = db.get(Question, question_id, options=[_OPCIONES])
    if pregunta is None or pregunta.topic.subject.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada.",
        )

    opciones_nuevas = None

    # Se recorre `model_fields_set` (los nombres de campo que el cliente
    # envio) en vez de `model_dump()`. Motivo: `model_dump` convierte todo en
    # diccionarios JSON, y las opciones volverian como una lista de dicts. Pero
    # `_construir_opciones` necesita los objetos `OptionInput` con sus
    # atributos. Leyendo con `getattr` sobre el esquema original, cada valor
    # conserva su tipo.
    for campo in datos.model_fields_set:
        if campo == "opciones":
            opciones_nuevas = datos.opciones
        else:
            setattr(pregunta, campo, getattr(datos, campo))

    if opciones_nuevas is not None:
        # --- ESTE ES EL TRAMPA IMPORTANTE ---
        # Hay que vaciar la lista y forzar el borrado ANTES de insertar las
        # nuevas. Sin el flush, PostgreSQL podria recibir primero el INSERT de
        # la nueva opcion correcta y despues el DELETE de la vieja, y ahi el
        # indice unico parcial se quejaria: "ya existe una correcta". El error
        # seria confuso y no tendria nada que ver con la peticion que fallo.
        pregunta.options.clear()
        db.flush()  # envia los DELETE a la base de inmediato
        pregunta.options = _construir_opciones(opciones_nuevas)

    db.commit()
    db.refresh(pregunta)
    return pregunta


# =============================================================================
# DELETE
# =============================================================================
@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pregunta(
    question_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Elimina una pregunta.

    OJO: esto tambien borra el historial de respuestas de los intentos donde
    se respondio, por el CASCADE de `answers`. Es el trade-off aceptado del
    MVP. En el frontend hay que pedir confirmacion.
    """
    pregunta = db.get(Question, question_id)
    if pregunta is None or pregunta.topic.subject.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada.",
        )

    db.delete(pregunta)
    db.commit()
