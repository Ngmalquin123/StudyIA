"""
StudyIA - Endpoints de materias (CRUD).

CRUD son las cuatro operaciones basicas:
  Create   -> POST   /api/subjects
  Read     -> GET    /api/subjects
  Update   -> PATCH  /api/subjects/{id}
  Delete   -> DELETE /api/subjects/{id}

Regla que se repite en TODO este archivo: cada consulta filtra por
`user_id`. No basta con poner el id en la URL; hay que comprobar que la
materia sea de quien pregunta.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user_id, get_db, get_subject_de_mi
from app.models import Subject
from app.schemas import SubjectCreate, SubjectRead, SubjectUpdate

router = APIRouter(prefix="/api/subjects", tags=["Materias"])


@router.post("", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
def crear_materia(
    datos: SubjectCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Crea una materia para el usuario que hace la peticion."""
    materia = Subject(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        color=datos.color,
        # El user_id NUNCA viene del cuerpo de la peticion. Lo pone el servidor
        # segun quien este autenticado. Si lo aceptáramos del cliente,
        # cualquiera podria crear materias en nombre de otro.
        user_id=user_id,
    )
    db.add(materia)
    db.commit()
    db.refresh(materia)  # recarga el objeto para traer el id que generó la BD
    return materia


@router.get("", response_model=list[SubjectRead])
def listar_materias(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Lista solo las materias del usuario. Sin parametro: siempre es el suyo."""
    consulta = select(Subject).where(Subject.user_id == user_id).order_by(Subject.nombre)
    return db.scalars(consulta).all()


@router.get("/{subject_id}", response_model=SubjectRead)
def obtener_materia(
    subject_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Devuelve una materia concreta, o 404 si no existe o no es del usuario."""
    return get_subject_de_mi(subject_id, user_id, db)


@router.patch("/{subject_id}", response_model=SubjectRead)
def actualizar_materia(
    subject_id: int,
    datos: SubjectUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Actualiza una materia parcialmente: solo cambia lo que viene en el cuerpo.

    Se usa PATCH y no PUT a proposito. PUT significa "reemplaza el objeto
    entero", asi que habria que mandar todos los campos y un campo olvidado
    se borraria. PATCH solo toca lo indicado, que es lo que espera un formulario.
    """
    materia = get_subject_de_mi(subject_id, user_id, db)

    # exclude_unset=True es la clave: separa "no vine este campo" de
    # "vine con valor null". Sin esto, un PATCH que no menciona descripcion
    # la pondria a NULL y borraria el texto sin querer.
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(materia, campo, valor)

    db.commit()
    db.refresh(materia)
    return materia


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_materia(
    subject_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Elimina una materia.

    No se borran los temas, preguntas, intentos ni progreso a mano: los
    `ON DELETE CASCADE` de la base se encargan. Un solo DELETE y listo.
    """
    materia = get_subject_de_mi(subject_id, user_id, db)
    db.delete(materia)
    db.commit()
    # 204 = "No Content": correcto, no hay nada que devolver.
    # Por eso la funcion no devuelve nada.
