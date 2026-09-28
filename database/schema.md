# Esquema de la base de datos - StudyIA

Documento de referencia de las 9 tablas del proyecto.

> **La fuente de verdad del esquema no es este documento**, sino los modelos de
> `backend/app/models.py` y la migración de `backend/alembic/versions/`.
> Si este documento y el código se contradicen, el código gana: hay que
> actualizar este archivo.

---

## Cómo se ve el conjunto

Los datos fluyen en cascada hacia abajo: cada nivel pertenece al anterior.

```
users          Una cuenta de estudiante
  |
  +-- subjects        Materia. Pertenece a UN usuario.
        |
        +-- topics         Tema dentro de una materia
              |
              +-- questions    Pregunta de un tema
              |     |
              |     +-- options    Opciones de respuesta (4 o mas)
              |
              +-- attempts     Un intento de resolver el tema
              |     |
              |     +-- answers   La respuesta dada a cada pregunta
              |
              +-- progress     Progreso acumulado del usuario en el tema

users
  +-- attempts
  +-- progress
  +-- recommendations   Que tema reforzar y por que
```

## Decisiones de diseno

### 1. Las materias son privadas

`subjects.user_id` es obligatorio. No existe una tabla de "inscripciones" ni de
roles: cada estudiante es dueno de sus materias y nadie mas las ve. Es una
decision consciente del MVP, no un accidente. Si manana hace falta que un
profesor comparta materias, habria que agregar una tabla intermedia y cambiar
esta regla.

### 2. Todo se borra en cascada

Cada llave forena declara `ON DELETE CASCADE`. Consecuencia directa: si un
estudiante borra su materia, PostgreSQL borra solo los temas, preguntas,
opciones, intentos, respuestas y registros de progreso que colgaban de ella.
No hay basura huerfana en la base.

> **Aviso importante:** `answers` tambien tiene `ON DELETE CASCADE` hacia
> `questions` y `options`. Eso significa que **borrar una pregunta elimina el
> historial de respuestas de los intentos**. Cuando se implemente el borrado de
> preguntas (Fase 3), el backend deberia avisar al usuario antes de borrar si la
> pregunta ya fue respondida. Es un trade-off aceptado para el MVP.

### 3. La base de datos es la ultima linea de defensa

Las reglas Criticas se imponen con restricciones de SQL, no solo con codigo
Python. Si un bug en el backend intenta violarlas, la base lo rechaza igual.

| Regla | Como se implementa | Archivo |
|---|---|---|
| Maximo 1 opcion correcta por pregunta | Indice unico **parcial** | `options` |
| No repetir email | `UNIQUE` en `users.email` | `users` |
| Dificultad entre 1 y 5 | `CHECK` | `questions` |
| Origen solo `manual` o `ia` | `CHECK` | `questions` |
| Un intento tiene al menos 1 pregunta | `CHECK` | `attempts` |
| Aciertos no superan preguntas | `CHECK` | `progress` |
| 1 registro de progreso por tema | `UNIQUE(user_id, topic_id)` | `progress` |
| 1 respuesta por pregunta en un intento | `UNIQUE(attempt_id, question_id)` | `answers` |
| Estado de recomendacion valido | `CHECK` | `recommendations` |

### 4. Por que el indice de `options` es PARCIAL

Es el detalle mas importante del esquema, asi que vale la pena explicarlo.

Una pregunta tiene varias opciones. La regla dice: **como maximo una puede ser
correcta**. Un `UNIQUE` normal en `question_id` estaria mal, porque prohibiria
tener varias opciones *incorrectas* (que es lo normal: 1 correcta + 3
incorrectas).

La solucion es un indice unico que solo mira las filas que nos interesan:

```sql
CREATE UNIQUE INDEX uq_options_una_sola_correcta
    ON options (question_id)
    WHERE es_correcta = true;
```

PostgreSQL solo considera las filas con `es_correcta = true` al aplicar la
unicidad. Las incorrectas quedan libres.

**Lo que NO garantiza:** la base permite que una pregunta tenga *cero* opciones
correctas. "Como maximo una" y "exactamente una" son cosas distintas. La regla
de "exactamente una" la debe validar el backend, porque es una regla de
negocio, no de integridad. Queda anotado para la Fase 3.

### 5. `answers.es_correcta` es una copia, a proposito

Podriamos deducir si la respuesta fue correcta mirando `options.es_correcta`. Se
guarda igual en `answers` para que, si el estudiante edita una pregunta y
cambia cual era la opcion correcta, **su historial no cambie retroactivamente**.
El resultado historico queda congelado en el momento en que se respondió.

### 6. Valores numericos

- `dificultad` y `orden` usan `SMALLINT` (numeros chicos, 0 a 32767).
- `porcentaje` usa `NUMERIC(5,2)`: maximo 999.99 con 2 decimales.
  Se prefiere sobre `FLOAT` para porcentajes porque evita errores de redondeo
  tipicos de los numeros de punto flotante.

---

## Las 9 tablas en detalle

### `users` - cuentas de estudiantes

| Columna | Tipo | Reglas | Descripcion |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement | Identificador unico |
| `nombre` | VARCHAR(120) | obligatorio | Nombre del estudiante |
| `email` | VARCHAR(255) | obligatorio, **UNIQUE**, indexado | Se usa para iniciar sesion |
| `password_hash` | VARCHAR(255) | obligatorio | Hash de la contrasena, **nunca** la contrasena |
| `activo` | BOOLEAN | obligatorio, por defecto `true` | Permite desactivar sin borrar |
| `creado_en` | TIMESTAMPTZ | obligatorio, por defecto `now()` | Fecha de registro |

### `subjects` - materias

| Columna | Tipo | Reglas | Descripcion |
|---|---|---|---|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK -> `users.id`, **CASCADE**, obligatorio, indexado | Dueño de la materia |
| `nombre` | VARCHAR(120) | obligatorio | |
| `descripcion` | TEXT | opcional | |
| `color` | VARCHAR(7) | opcional | Formato `#RRGGBB`, lo usa el frontend |
| `creado_en` | TIMESTAMPTZ | obligatorio, `now()` | |

### `topics` - temas de una materia

| Columna | Tipo | Reglas | Descripcion |
|---|---|---|---|
| `id` | INTEGER | PK | |
| `subject_id` | INTEGER | FK -> `subjects.id`, **CASCADE**, obligatorio, indexado | |
| `nombre` | VARCHAR(150) | obligatorio | |
| `descripcion` | TEXT | opcional | |
| `creado_en` | TIMESTAMPTZ | obligatorio, `now()` | |

### `questions` - preguntas

| Columna | Tipo | Reglas | Descripcion |
|---|---|---|---|
| `id` | INTEGER | PK | |
| `topic_id` | INTEGER | FK -> `topics.id`, **CASCADE**, obligatorio, indexado | |
| `enunciado` | TEXT | obligatorio | Texto de la pregunta |
| `dificultad` | SMALLINT | obligatorio, por defecto `1`, **CHECK 1-5** | |
| `origen` | VARCHAR(10) | obligatorio, por defecto `manual`, **CHECK** | `manual` o `ia` |
| `creado_en` | TIMESTAMPTZ | obligatorio, `now()` | |

### `options` - opciones de respuesta

| Columna | Tipo | Reglas | Descripcion |
|---|---|---|---|
| `id` | INTEGER | PK | |
| `question_id` | INTEGER | FK -> `questions.id`, **CASCADE**, obligatorio, indexado | |
| `texto` | TEXT | obligatorio | Texto de la opcion |
| `es_correcta` | BOOLEAN | obligatorio, por defecto `false` | Participa del indice parcial |
| `orden` | SMALLINT | obligatorio, por defecto `0` | Posicion (A, B, C, D) |

Indice parcial: `uq_options_una_sola_correcta` (ver seccion 4).

### `attempts` - intentos

| Columna | Tipo | Reglas | Descripcion |
|---|---|---|---|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK -> `users.id`, **CASCADE**, indexado | |
| `topic_id` | INTEGER | FK -> `topics.id`, **CASCADE**, indexado | |
| `correctas` | INTEGER | obligatorio | Numero de aciertos |
| `total` | INTEGER | obligatorio, **CHECK > 0** | Numero de preguntas respondidas |
| `porcentaje` | NUMERIC(5,2) | obligatorio | `correctas / total * 100` |
| `duracion_segundos` | INTEGER | opcional | Tiempo que tardo el estudiante |
| `fecha` | TIMESTAMPTZ | obligatorio, `now()`, indexado | |

### `answers` - respuestas dentro de un intento

| Columna | Tipo | Reglas | Descripcion |
|---|---|---|---|
| `id` | INTEGER | PK | |
| `attempt_id` | INTEGER | FK -> `attempts.id`, **CASCADE**, indexado | |
| `question_id` | INTEGER | FK -> `questions.id`, **CASCADE**, indexado | |
| `option_id` | INTEGER | FK -> `options.id`, **CASCADE**, indexado | Opcion elegida |
| `es_correcta` | BOOLEAN | obligatorio | Copia del resultado al momento de responder |

`UNIQUE(attempt_id, question_id)`: una sola respuesta por pregunta e intento.

### `progress` - progreso acumulado

Una sola fila por combinacion de estudiante y tema. Se actualiza (no se
duplica) cada vez que se registra un intento.

| Columna | Tipo | Reglas | Descripcion |
|---|---|---|---|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK -> `users.id`, **CASCADE**, indexado | |
| `topic_id` | INTEGER | FK -> `topics.id`, **CASCADE**, indexado | |
| `total_intentos` | INTEGER | por defecto `0`, **CHECK >= 0** | |
| `total_preguntas` | INTEGER | por defecto `0` | Suma de preguntas de todos los intentos |
| `total_aciertos` | INTEGER | por defecto `0`, **CHECK <= total_preguntas** | |
| `porcentaje` | NUMERIC(5,2) | por defecto `0` | `total_aciertos / total_preguntas * 100` |
| `ultima_actividad` | TIMESTAMPTZ | opcional | Ultima vez que practic |

`UNIQUE(user_id, topic_id)`: garantiza una unica fila de progreso por tema.

### `recommendations` - recomendaciones

| Columna | Tipo | Reglas | Descripcion |
|---|---|---|---|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK -> `users.id`, **CASCADE**, indexado | |
| `topic_id` | INTEGER | FK -> `topics.id`, **CASCADE**, indexado | |
| `porcentaje_obtenido` | NUMERIC(5,2) | opcional | El % que motivo la recomendacion |
| `motivo` | TEXT | obligatorio | **Por que** se recomienda (obligatorio, para poder explicarlo) |
| `estado` | VARCHAR(10) | por defecto `pendiente`, **CHECK** | `pendiente`, `visto`, `completado` |
| `creado_en` | TIMESTAMPTZ | obligatorio, `now()` | |

---

## Operaciones con Alembic

Siempre desde la carpeta `backend/`, con el entorno virtual activo.

```bash
# Aplicar todo lo pendiente
alembic upgrade head

# Ver donde estamos
alembic current

# Ver que cambios faltan entre el codigo y la base
alembic check

# Crear una migracion nueva despues de cambiar los modelos
alembic revision --autogenerate -m "descripcion del cambio"

# Deshacer la ultima migracion
alembic downgrade -1
```

**Regla de oro:** despues de `autogenerate`, SIEMPRE leer el archivo generado
antes de aplicarlo. Alembic es una herramienta, no un adivino. Puede generar
una columna sin el tipo correcto o un borrado que no querias.

**Regla de oro 2:** en la base de datos, las secuencias (`*_id_seq`) no se
revierten con un `ROLLBACK`. Si pruebas inserciones y luego haces rollback, los
ids consumidos se pierden para siempre y el siguiente registro empieza en un
numero mayor. No es un bug, es como funciona PostgreSQL.
