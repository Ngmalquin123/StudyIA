"""
StudyIA - Esquemas de validacion (capa Pydantic).

Un "esquema" describe la forma exacta de un dato que entra o sale de la API.
Su trabajo es triple:

  1. Validar que el dato tenga sentido ANTES de tocar la base de datos.
  2. Evitar que la base reciba columnas que no existen.
  3. Ocultar informacion que el cliente no debe ver.

La diferencia con los modelos (`models.py`):

  - `models.py`  -> como es la TABLA. Habla con la base de datos.
  - `schemas.py` -> como es el DATO por la API. Habla con el exterior.

No es lo mismo. No hay que revisar la documentacion de Swagger para saber que
acepta cada endpoint: las clases de este archivo lo dicen.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# =============================================================================
# BASE
# =============================================================================
class ORMBase(BaseModel):
    """
    Base de todos los esquemas que se leen desde la base de datos.

    `from_attributes=True` le dice a Pydantic: "este esquema se construye a
    partir de un objeto de SQLAlchemy, lee sus atributos". Sin esto, Pydantic
    pedirria un diccionario y fallaria con los objetos del ORM.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# MATERIAS (subjects)
# =============================================================================
class SubjectCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=120, examples=["Cálculo diferencial"])
    descripcion: str | None = Field(default=None, max_length=500, examples=["Límites y derivadas"])
    # description en el campo, no en el codigo: Swagger lo muestra y el
    # frontend recibe la validacion gratis.
    color: str | None = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Color hexadecimal, por ejemplo #4F46E5",
        examples=["#4F46E5"],
    )


class SubjectUpdate(BaseModel):
    """
    Todos los campos son opcionales: en un PATCH solo se actualiza lo que viene.

    Importante: no se manda `id` ni `user_id`. El id lo pone la URL y el
    propietario es el del token. Si el cliente pudiera enviarlos, podria
    cambiar el dueño de una materia ajena.
    """

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = Field(default=None, max_length=500)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class SubjectRead(ORMBase):
    id: int
    nombre: str
    descripcion: str | None
    color: str | None
    creado_en: datetime


# =============================================================================
# TEMAS (topics)
# =============================================================================
class TopicCreate(BaseModel):
    # ge=1 impide enviar un subject_id=0 o negativo, que no existe.
    subject_id: int = Field(ge=1, examples=[1])
    nombre: str = Field(min_length=1, max_length=150, examples=["Límites"])
    descripcion: str | None = Field(default=None, max_length=500)


class TopicUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = Field(default=None, max_length=500)


class TopicRead(ORMBase):
    id: int
    subject_id: int
    nombre: str
    descripcion: str | None
    creado_en: datetime


# =============================================================================
# OPCIONES (options)
# =============================================================================
class OptionInput(BaseModel):
    """Una opcion tal como la envia el cliente al crear o editar una pregunta."""

    texto: str = Field(min_length=1, examples=["El limite no existe"])
    es_correcta: bool = Field(default=False)
    # Opcional: si no se envia, el backend le asigna la posicion (1, 2, 3...).
    orden: int | None = Field(default=None, ge=1)


class OptionRead(ORMBase):
    """Opcion CON la respuesta correcta. Solo para editar y para el admin."""

    id: int
    texto: str
    es_correcta: bool
    orden: int


class OptionSafeRead(ORMBase):
    """
    Opcion SIN la respuesta correcta. Es la que ve el estudiante al practicar.

    Este esquema existe para que sea imposible por accidente filtrar la
    solucion: aunque el endpoint que usa este esquema cargue el objeto
    completo de SQLAlchemy, Pydantic solo copiara estos 3 campos.
    """

    id: int
    texto: str
    orden: int


# =============================================================================
# PREGUNTAS (questions)
# =============================================================================
class QuestionCreate(BaseModel):
    topic_id: int = Field(ge=1, examples=[1])
    enunciado: str = Field(
        min_length=5,
        examples=["Cual es el limite de (sin x - sin 2x) / x cuando x tiende a 0?"],
    )
    dificultad: int = Field(default=1, ge=1, le=5, examples=[3])
    origen: Literal["manual", "ia"] = Field(default="manual", examples=["manual"])
    # min_length=2: una pregunta con una sola opcion no es una pregunta.
    opciones: list[OptionInput] = Field(min_length=2, max_length=10)

    @model_validator(mode="after")
    def exactamente_una_correcta(self) -> "QuestionCreate":
        """
        Valida que haya EXACTAMENTE una opcion correcta.

        ESTA es la regla que la base de datos no puede imposed. El indice
        unico parcial de `options` garantiza "como maximo una", pero permitiria
        cero. Una pregunta sin opcion correcta esta rota y el estudiante no
        podria acertarla nunca, asi que se rechaza antes de guardar.
        """
        correctas = [o for o in self.opciones if o.es_correcta]
        if len(correctas) != 1:
            raise ValueError(
                f"Una pregunta debe tener exactamente 1 opcion correcta, "
                f"y se recibieron {len(correctas)}. "
                f"Marca una opcion con es_correcta=true."
            )
        return self


class QuestionUpdate(BaseModel):
    enunciado: str | None = Field(default=None, min_length=5)
    dificultad: int | None = Field(default=None, ge=1, le=5)
    origen: Literal["manual", "ia"] | None = None
    opciones: list[OptionInput] | None = Field(default=None, min_length=2, max_length=10)

    @model_validator(mode="after")
    def exactamente_una_correcta_si_vienen(self) -> "QuestionUpdate":
        """
        Solo se valida si vienen opciones. Un PATCH que solo cambia el
        enunciado no tiene por que reenviar la lista entera.
        """
        if self.opciones is not None:
            correctas = [o for o in self.opciones if o.es_correcta]
            if len(correctas) != 1:
                raise ValueError(
                    f"La lista de opciones debe tener exactamente 1 correcta, "
                    f"y se recibieron {len(correctas)}."
                )
        return self


class QuestionRead(ORMBase):
    """
    Pregunta SIN la respuesta correcta. Es lo que recibe el estudiante al
    practicar. Notese que no tiene `es_correcta` en ningun nivel.
    """

    id: int
    topic_id: int
    enunciado: str
    dificultad: int
    origen: str
    # El campo de la API se llama "opciones", pero el atributo en el modelo
    # SQLAlchemy se llama "options". `validation_alias` le dice a Pydantic que
    # para rellenar este campo debe leer "options" del objeto. En la respuesta
    # JSON sigue apareciendo como "opciones", que es lo que ve el frontend.
    opciones: list[OptionSafeRead] = Field(validation_alias="options")


class QuestionDetail(QuestionRead):
    """
    Pregunta CON las respuestas correctas. Solo para editar y revisar.

    Nota de seguridad: este esquema no debe usarse en ningun endpoint que el
    estudiante consulte mientras practica. Si se usa, el estudiante puede
    abrir las herramientas de desarrollo del navegador y leer la solucion.
    """

    opciones: list[OptionRead] = Field(validation_alias="options")
