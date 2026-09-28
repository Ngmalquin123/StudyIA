"""
StudyIA - Datos de demostracion.

Crea usuarios de prueba para poder probar el CRUD. Hace falta porque el
CRUD (Fase 3) se desarrollo ANTES que el login (Fase 4): sin usuarios en la
tabla `users`, cualquier intento de crear una materia falla con un error de
llave forena, porque toda materia pertenece a un usuario.

Como todavia no hay endpoint de registro, este script inserta directo en la
base. En la Fase 4 el usuario se crea desde la API y este script pasara a
servir solo para datos de demostracion.

USO:
    python seed_demo.py

Es idempotente: si lo ejecutas dos veces no duplica nada.
"""

import bcrypt
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Option, Question, Subject, Topic, User

# Contrasena de los usuarios demo. Es de prueba y publica a proposito.
# En accounts reales esto no existe: la contrasena la elige el usuario.
CONTRASENA_DEMO = "demo1234"

USUARIOS_DEMO = [
    {
        "nombre": "Ana Torres",
        "email": "ana@studyia.test",
        "activo": True,
    },
    {
        "nombre": "Luis Ramirez",
        "email": "luis@studyia.test",
        "activo": True,
    },
]

# Contenido academico de ejemplo. El indice es la posicion en la lista de
# usuarios: 0 = Ana, 1 = Luis. Asi cada uno ve algo distinto y se nota de
# inmediato si el aislamiento por usuario deja de funcionar.
CONTENIDO_DEMO = [
    {
        "indice_usuario": 0,
        "materias": [
            {
                "nombre": "Calculo diferencial",
                "descripcion": "Limites, derivadas e integrales",
                "color": "#4F46E5",
                "temas": [
                    {
                        "nombre": "Limites",
                        "descripcion": "Limites laterales y al infinito",
                        "preguntas": [
                            {
                                "enunciado": "Cual es el limite de (sen x)/x cuando x tiende a 0?",
                                "dificultad": 2,
                                "opciones": [
                                    ("1", True),
                                    ("0", False),
                                    ("No existe", False),
                                    ("Indefinido", False),
                                ],
                            },
                            {
                                "enunciado": "Que valor toma (x^2 - 4) / (x - 2) en x = 2?",
                                "dificultad": 3,
                                "opciones": [
                                    ("0", False),
                                    ("2", False),
                                    ("4", True),
                                    ("No existe", False),
                                ],
                            },
                        ],
                    },
                    {
                        "nombre": "Derivadas",
                        "descripcion": "Reglas de derivacion",
                        "preguntas": [
                            {
                                "enunciado": "Cual es la derivada de (sen x) en x = 0?",
                                "dificultad": 1,
                                "opciones": [
                                    ("0", True),
                                    ("1", False),
                                    ("-1", False),
                                    ("No existe", False),
                                ],
                            }
                        ],
                    },
                ],
            },
            {
                "nombre": "Estadistica",
                "descripcion": "Probabilidad basica",
                "color": "#059669",
                "temas": [
                    {
                        "nombre": "Probabilidad",
                        "descripcion": "Eventos independientes",
                        "preguntas": [
                            {
                                "enunciado": "Cual es la probabilidad de obtener 6 al lanzar un dado?",
                                "dificultad": 1,
                                "opciones": [
                                    ("1/6", True),
                                    ("1/3", False),
                                    ("1/2", False),
                                    ("6", False),
                                ],
                            }
                        ],
                    }
                ],
            },
        ],
    },
    {
        "indice_usuario": 1,
        "materias": [
            {
                "nombre": "Algebra lineal",
                "descripcion": "Matrices y espacios vectoriales",
                "color": "#DC2626",
                "temas": [
                    {
                        "nombre": "Matrices",
                        "descripcion": "Determinantes",
                        "preguntas": [
                            {
                                "enunciado": "Cual es el determinante de una matriz identidad de 3x3?",
                                "dificultad": 1,
                                "opciones": [
                                    ("0", False),
                                    ("1", True),
                                    ("3", False),
                                    ("9", False),
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    },
]


def hashear(contrasena: str) -> str:
    """
    Convierte una contrasena en su hash.

    Un hash es una huella unidireccional: se puede comprobar que una
    contrasena coincide, pero no se puede recuperar la original. Por eso la
    base guarda el hash y nunca la contrasena.

    `gensalt()` genera una "sal" aleatoria en cada llamada, de modo que dos
    usuarios con la MISMA contrasena tienen hashes DISTINTOS. Sin sal, un
    atacante podria comparar hashes y descubrir que dos cuentas comparten
    clave.
    """
    sal = bcrypt.gensalt()
    return bcrypt.hashpw(contrasena.encode("utf-8"), sal).decode("utf-8")


def sembrar_contenido(db, usuarios: list[User]) -> tuple[int, int]:
    """
    Crea materias, temas, preguntas y opciones para los usuarios demo.

    Devuelve (materias_creadas, preguntas_creadas).
    """
    materias_nuevas = 0
    preguntas_nuevas = 0

    for bloque in CONTENIDO_DEMO:
        usuario = usuarios[bloque["indice_usuario"]]

        for datos_materia in bloque["materias"]:
            materia = Subject(
                user_id=usuario.id,
                nombre=datos_materia["nombre"],
                descripcion=datos_materia["descripcion"],
                color=datos_materia["color"],
            )
            db.add(materia)
            db.flush()  # necesitamos el id de la materia ya para los temas
            materias_nuevas += 1

            for datos_tema in datos_materia["temas"]:
                tema = Topic(
                    subject_id=materia.id,
                    nombre=datos_tema["nombre"],
                    descripcion=datos_tema["descripcion"],
                )
                db.add(tema)
                db.flush()

                for datos_pregunta in datos_tema["preguntas"]:
                    pregunta = Question(
                        topic_id=tema.id,
                        enunciado=datos_pregunta["enunciado"],
                        dificultad=datos_pregunta["dificultad"],
                        origen="manual",
                    )
                    # El orden se asigna aqui, no se pide en los datos.
                    for posicion, (texto, correcta) in enumerate(
                        datos_pregunta["opciones"], start=1
                    ):
                        pregunta.options.append(
                            Option(texto=texto, es_correcta=correcta, orden=posicion)
                        )
                    db.add(pregunta)
                    preguntas_nuevas += 1

    return materias_nuevas, preguntas_nuevas


def main() -> None:
    db = SessionLocal()
    try:
        creados = 0
        existentes = 0
        emails: list[str] = []

        for datos in USUARIOS_DEMO:
            ya_existe = db.scalar(
                select(User).where(User.email == datos["email"])
            )
            if ya_existe:
                print(f"  = {datos['email']:24} ya existia, no se toca")
                existentes += 1
            else:
                db.add(
                    User(
                        nombre=datos["nombre"],
                        email=datos["email"],
                        password_hash=hashear(CONTRASENA_DEMO),
                        activo=datos["activo"],
                    )
                )
                print(f"  + {datos['email']:24} creado")
                creados += 1
            emails.append(datos["email"])

        db.commit()

        # El contenido solo se siembra si la base estaba vacia de usuarios.
        # Asi el script se puede reejecutar sin duplicar materias.
        if creados > 0:
            usuarios = db.scalars(
                select(User).where(User.email.in_(emails))
            ).all()
            materias, preguntas = sembrar_contenido(db, usuarios)
            db.commit()
            print(f"\n  + {materias} materias con {preguntas} preguntas de ejemplo")

        print(f"\nListo. {creados} usuarios creados, {existentes} ya existian.")
        print(f"Contrasena de todos: {CONTRASENA_DEMO}")

        todos = db.scalars(select(User).order_by(User.id)).all()
        print("\nPara probar el aislamiento, abre Swagger en /docs y pon")
        print("la cabecera X-User-Id con el id del usuario que quieras ser:")
        for usuario in todos:
            print(f"  X-User-Id: {usuario.id}   ({usuario.nombre})")
    finally:
        # finally = pase lo que pase, se cierra la conexion.
        db.close()


if __name__ == "__main__":
    print("Creando datos de demostracion...\n")
    main()
