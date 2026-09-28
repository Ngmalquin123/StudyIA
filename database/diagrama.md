# Diagrama de la base de datos - StudyIA

Diagrama entidad-relacion de las 9 tablas. El detalle de cada columna esta en
[`schema.md`](./schema.md).

## Diagrama

```mermaid
erDiagram
    USERS ||--o{ SUBJECTS       : "crea"
    USERS ||--o{ ATTEMPTS       : "realiza"
    USERS ||--o{ PROGRESS       : "acumula"
    USERS ||--o{ RECOMMENDATIONS : "recibe"

    SUBJECTS ||--o{ TOPICS      : "contiene"
    SUBJECTS ||--o{ TOPICS      : "borrar materia borra temas"

    TOPICS ||--o{ QUESTIONS     : "agrupa"
    TOPICS ||--o{ ATTEMPTS      : "se practica en"
    TOPICS ||--o{ PROGRESS      : "se mide en"
    TOPICS ||--o{ RECOMMENDATIONS : "se recomienda"

    QUESTIONS ||--o{ OPTIONS    : "ofrece"
    QUESTIONS ||--o{ ANSWERS    : "es respondida en"

    ATTEMPTS ||--o{ ANSWERS     : "contiene respuestas"
    OPTIONS ||--o{ ANSWERS      : "es elegida en"

    USERS {
        int         id           PK
        varchar     nombre
        varchar     email        UK "unico, indexado"
        varchar     password_hash "hash, nunca la contrasena"
        boolean     activo       "por defecto true"
        timestamptz creado_en    "por defecto now()"
    }

    SUBJECTS {
        int         id           PK
        int         user_id      FK "CASCADE, obligatorio"
        varchar     nombre
        text        descripcion  "opcional"
        varchar     color        "opcional, #RRGGBB"
        timestamptz creado_en    "por defecto now()"
    }

    TOPICS {
        int         id           PK
        int         subject_id   FK "CASCADE, obligatorio"
        varchar     nombre
        text        descripcion  "opcional"
        timestamptz creado_en    "por defecto now()"
    }

    QUESTIONS {
        int         id           PK
        int         topic_id     FK "CASCADE, obligatorio"
        text        enunciado
        smallint    dificultad   "CHECK 1-5, por defecto 1"
        varchar     origen       "CHECK: manual | ia, por defecto manual"
        timestamptz creado_en    "por defecto now()"
    }

    OPTIONS {
        int         id           PK
        int         question_id  FK "CASCADE, obligatorio"
        text        texto
        boolean     es_correcta  "por defecto false"
        smallint    orden        "por defecto 0"
    }

    ATTEMPTS {
        int         id               PK
        int         user_id          FK "CASCADE"
        int         topic_id         FK "CASCADE"
        int         correctas
        int         total            "CHECK > 0"
        decimal     porcentaje       "NUMERIC(5,2)"
        int         duracion_segundos "opcional"
        timestamptz fecha            "por defecto now()"
    }

    ANSWERS {
        int         id           PK
        int         attempt_id   FK "CASCADE"
        int         question_id  FK "CASCADE"
        int         option_id    FK "CASCADE"
        boolean     es_correcta  "copia congelada del resultado"
    }

    PROGRESS {
        int         id                PK
        int         user_id           FK "CASCADE"
        int         topic_id          FK "CASCADE"
        int         total_intentos    "por defecto 0"
        int         total_preguntas   "por defecto 0"
        int         total_aciertos    "por defecto 0"
        decimal     porcentaje        "NUMERIC(5,2), por defecto 0"
        timestamptz ultima_actividad  "opcional"
    }

    RECOMMENDATIONS {
        int         id                 PK
        int         user_id            FK "CASCADE"
        int         topic_id           FK "CASCADE"
        decimal     porcentaje_obtenido "opcional"
        text        motivo             "por que se recomienda"
        varchar     estado             "CHECK: pendiente | visto | completado"
        timestamptz creado_en         "por defecto now()"
    }
```

## Como leerlo

**`||--o{`** significa "uno tiene muchos". Por ejemplo, `USERS ||--o{ SUBJECTS`:
un usuario tiene muchas materias, y cada materia pertenece a un solo usuario.

**`PK`** = llave primaria (identificador unico de la fila).
**`FK`** = llave forena (apunta a otra tabla).
**`UK`** = llave unica (no se puede repetir).
**`CASCADE`** = si se borra la fila apuntada, esta fila se borra sola.
**`CHECK`** = regla que valida un valor allowed range o una lista.
Las comillas en los atributos son comentarios explicativos.

## Diagrama de flujo: como se usa un tema

```mermaid
flowchart TD
    U[Estudiante] -->|crea| S[Materia]
    S -->|contiene| T[Tema]
    T -->|tiene| Q[Preguntas]
    Q -->|tiene| O[Opciones<br/>1 correcta + 3 incorrectas]

    U -->|intenta resolver| A[Intento]
    T --> A
    A -->|registra| AN[Respuestas]
    O --> AN

    A -->|actualiza| P[Progreso<br/>1 fila por usuario y tema]

    P -->|si el % es bajo| R[Recomendacion<br/>con su motivo]
    R -->|vuelve a| T
```

## Diagrama de flujo: por que se borra todo en cascada

```mermaid
flowchart TD
    D["DELETE FROM subjects"] -->|CASCADE| DT[topics]
    DT -->|CASCADE| DQ[questions]
    DQ -->|CASCADE| DO[options]

    DT -->|CASCADE| DA[attempts]
    DA -->|CASCADE| DAN[answers]
    DO -->|CASCADE| DAN

    DT -->|CASCADE| DP[progress]
    DT -->|CASCADE| DR[recommendations]

    style D fill:#ffdddd,stroke:#cc0000
    style DAN fill:#ffdddd,stroke:#cc0000
    style DO fill:#ffdddd,stroke:#cc0000
```

Un solo `DELETE` limpia las 6 tablas dependientes. Por eso `answers` tiene
tambien `CASCADE` hacia `questions` y `options`: borrar una pregunta
**destruye el historial de respuestas**. Ver el aviso en
[`schema.md`](./schema.md), seccion 2.
