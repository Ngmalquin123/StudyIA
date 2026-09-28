"""
StudyIA - Modelos de la base de datos (capa ORM).

Cada clase de aqui corresponde a UNA tabla de PostgreSQL. SQLAlchemy traduce
estas clases a SQL por nosotros, asi que casi nunca escribimos SQL a mano.

Orden de lectura de este archivo (de arriba hacia abajo va de lo general a
lo especifico): User, Subject, Topic, Question, Option, Attempt, Answer,
Progress, Recommendation.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# =============================================================================
# USERS - las cuentas de los estudiantes
# =============================================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    # unique=True + index=True: no puede haber dos cuentas con el mismo email,
    # y ademas la busqueda por email es rapida.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # NUNCA se guarda la contrasena. Solo su hash: un texto que no se puede
    # deshacer. Si alguien lee la base, no puede saber las contrasenas.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    attempts: Mapped[list["Attempt"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    progress: Mapped[list["Progress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.id} {self.email}>"


# =============================================================================
# SUBJECTS - las materias de cada estudiante
# =============================================================================
class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Toda materia pertenece a un usuario. ESTA es la columna que garantiza
    # que un estudiante no vea las materias de otro.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Color en formato "#RRGGBB", lo usa el frontend para pintar la etiqueta
    # de la materia. Opcional: si no se envia, el backend elige uno.
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="subjects")
    topics: Mapped[list["Topic"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Subject {self.id} {self.nombre}>"


# =============================================================================
# TOPICS - los temas dentro de una materia
# =============================================================================
class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    subject: Mapped["Subject"] = relationship(back_populates="topics")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan"
    )
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="topic")
    progress: Mapped[list["Progress"]] = relationship(back_populates="topic")

    def __repr__(self) -> str:
        return f"<Topic {self.id} {self.nombre}>"


# =============================================================================
# QUESTIONS - preguntas de opcion multiple
# =============================================================================
class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        # La dificultad solo puede ser de 1 a 5. Si alguien intenta guardar
        # un 99, la base de datos lo rechaza.
        CheckConstraint("dificultad BETWEEN 1 AND 5", name="ck_questions_dificultad"),
        # "manual" = escrita por el estudiante, "ia" = generada por Gemini.
        CheckConstraint("origen IN ('manual', 'ia')", name="ck_questions_origen"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    enunciado: Mapped[str] = mapped_column(Text, nullable=False)
    dificultad: Mapped[int] = mapped_column(
        SmallInteger, default=1, server_default=text("1"), nullable=False
    )
    origen: Mapped[str] = mapped_column(
        String(10), default="manual", server_default=text("'manual'"), nullable=False
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    topic: Mapped["Topic"] = relationship(back_populates="questions")
    options: Mapped[list["Option"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Question {self.id}>"


# =============================================================================
# OPTIONS - las opciones de respuesta de una pregunta
# =============================================================================
class Option(Base):
    __tablename__ = "options"
    __table_args__ = (
        # ---- EL DETALLE MAS IMPORTANTE DE ESTA TABLA ----
        # Indice unico PARCIAL: garantiza que exista como maximo UNA opcion
        # correcta por pregunta. El `where` limita la regla a las filas que
        # tienen es_correcta = true, asi que las opciones incorrectas pueden
        # repetirse libremente.
        #
        # No es que el codigo lo prohíba: es que la BASE DE DATOS no lo
        # permite. Si el codigo tuviera un error e intentara guardar dos
        # opciones correctas, PostgreSQL lanza un error y listo.
        Index(
            "uq_options_una_sola_correcta",
            "question_id",
            unique=True,
            postgresql_where=text("es_correcta = true"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    es_correcta: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    # Posicion de la opcion (A, B, C, D) para mantenerlas siempre en orden.
    orden: Mapped[int] = mapped_column(
        SmallInteger, default=0, server_default=text("0"), nullable=False
    )

    question: Mapped["Question"] = relationship(back_populates="options")

    def __repr__(self) -> str:
        return f"<Option {self.id} correcta={self.es_correcta}>"


# =============================================================================
# ATTEMPTS - un intento de responder las preguntas de un tema
# =============================================================================
class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (CheckConstraint("total > 0", name="ck_attempts_total_positivo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Se guardan los tres: los numeroscrudos por si hay que recalcular, y el
    # porcentaje ya calculado para no recalcularlo en cada lectura.
    correctas: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    porcentaje: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    duracion_segundos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="attempts")
    topic: Mapped["Topic"] = relationship(back_populates="attempts")
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Attempt {self.id} {self.correctas}/{self.total}>"


# =============================================================================
# ANSWERS - la respuesta que el estudiante dio a cada pregunta
# =============================================================================
class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (
        # Una sola respuesta por pregunta dentro de un intento. Impide
        # guardar duplicados si el estudiante hace doble clic.
        UniqueConstraint("attempt_id", "question_id", name="uq_answers_intento_pregunta"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("attempts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    option_id: Mapped[int] = mapped_column(
        ForeignKey("options.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Copia del resultado, a proposito. Podriamos deducirlo mirando options,
    # pero si manana el profesor corrige una pregunta, el historial del
    # estudiante NO debe cambiar retroactivamente.
    es_correcta: Mapped[bool] = mapped_column(Boolean, nullable=False)

    attempt: Mapped["Attempt"] = relationship(back_populates="answers")

    def __repr__(self) -> str:
        return f"<Answer {self.id} correcta={self.es_correcta}>"


# =============================================================================
# PROGRESS - el progreso acumulado de un estudiante en un tema
# =============================================================================
class Progress(Base):
    __tablename__ = "progress"
    __table_args__ = (
        # Un solo registro de progreso por (estudiante, tema). Es la fila que
        # se actualiza cada vez que se registra un intento nuevo.
        UniqueConstraint("user_id", "topic_id", name="uq_progress_usuario_tema"),
        CheckConstraint("total_intentos >= 0", name="ck_progress_intentos"),
        CheckConstraint("total_aciertos <= total_preguntas", name="ck_progress_aciertos"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    total_intentos: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    total_preguntas: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    total_aciertos: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    porcentaje: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0, server_default=text("0"), nullable=False
    )
    ultima_actividad: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="progress")
    topic: Mapped["Topic"] = relationship(back_populates="progress")

    def __repr__(self) -> str:
        return f"<Progress user={self.user_id} topic={self.topic_id} {self.porcentaje}%>"


# =============================================================================
# RECOMMENDATIONS - temas que el sistema sugiere reforzar
# =============================================================================
class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'visto', 'completado')",
            name="ck_recommendations_estado",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    porcentaje_obtenido: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    # POR QUE se recomienda. Sin esto la recomendacion seria una caja negra;
    # con esto el sistema puede explicar su propia decision.
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(10), default="pendiente", server_default=text("'pendiente'"), nullable=False
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation {self.id} estado={self.estado}>"
