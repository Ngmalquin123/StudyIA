"""
StudyIA - Conexion con la base de datos.

Define el "motor" (engine), como se crean las sesiones y de donde heredan
todas las tablas. En una aplicacion real esto seria UN archivo. Aqui esta
separado de models.py para que quede claro quien hace que.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# El motor es el objeto que mantiene las conexiones abiertas al servidor.
# pool_pre_ping=True hace un SELECT 1 antes de reutilizar una conexion:
# si PostgreSQL se reinicio (por ejemplo un apagón), la conexion muerta se
# detecta y se reemplaza sola en vez de romper la app.
#
# echo=True imprime en la terminal CADA consulta SQL que se manda a la base.
# Se activa con DB_ECHO=true en el .env y es la forma de demostrar que la API
# hace consultas de verdad y no datos inventados. En produccion se deja false.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)

# SessionLocal es una "fabrica" de sesiones. Cada peticion HTTP crea una
# sesion nueva y la cierra al terminar.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos de la base de datos."""


def get_db() -> Generator[Session, None, None]:
    """
    Dependencia de FastAPI: entrega una sesion de base de datos al endpoint
    y garantiza que se cierre al terminar, pase lo que pase.

    En los endpoints se usa con:  db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
