# Diagrama de la base de datos - StudyIA

Diagrama entidad-relación de las 6 tablas. El detalle de cada columna está en
[`schema.md`](./schema.md).

## Diagrama

```mermaid
erDiagram
    ROLES ||--o{ USERS          : "asigna"

    USERS ||--o{ PROGRESS       : "acumula"
    USERS ||--o{ ACTIVITIES     : "registra"

    TOPICS ||--o{ QUESTIONS     : "agrupa"
    TOPICS ||--o{ PROGRESS      : "se mide en"

    ROLES {
        bigint      id       PK
        text        nombre   UK "admin | estudiante"
    }

    USERS {
        bigint      id       PK
        text        name
        text        email    UK "único, en minúsculas"
        text        password "hash argon2, nunca la contraseña"
        bigint      rol_id   FK "SET NULL, opcional"
    }

    TOPICS {
        bigint      id           PK
        text        name
        text        description  "opcional"
    }

    QUESTIONS {
        bigint      id              PK
        bigint      topic_id        FK "CASCADE"
        text        question
        text        correct_answer
        text_array  options         "TEXT[], opcional"
    }

    PROGRESS {
        bigint      id            PK
        bigint      user_id       FK "CASCADE"
        bigint      topic_id      FK "CASCADE"
        text        level         "opcional"
        timestamptz last_updated  "por defecto now()"
    }

    ACTIVITIES {
        bigint      id       PK
        bigint      user_id  FK "CASCADE"
        text        type
        text        content  "opcional"
        timestamptz date     "por defecto now()"
    }
```

## Cómo leerlo

**`||--o{`** significa "uno tiene muchos". Por ejemplo, `ROLES ||--o{ USERS`:
un rol lo tienen muchos usuarios y cada usuario tiene un solo rol.

**`PK`** = llave primaria. **`FK`** = llave foránea. **`UK`** = valor único.
**`CASCADE`** = si se borra la fila apuntada, esta fila se borra sola.
**`SET NULL`** = si se borra la fila apuntada, esta columna queda en `NULL`.

## Flujo de autenticación

```mermaid
flowchart TD
    R[POST /api/auth/register] -->|hash argon2| U[(users)]
    RO[(roles)] -->|rol 'estudiante'| U
    L[POST /api/auth/login] -->|verifica hash| U
    L -->|devuelve| T[Token JWT]
    T -->|Authorization: Bearer| M[GET /api/auth/me]
    M -->|lee| U
```

## Qué se borra en cascada

```mermaid
flowchart TD
    DU["DELETE FROM users"] -->|CASCADE| P[progress]
    DU -->|CASCADE| A[activities]

    DT["DELETE FROM topics"] -->|CASCADE| Q[questions]
    DT -->|CASCADE| P

    DR["DELETE FROM roles"] -->|SET NULL| U["users.rol_id = NULL"]

    style DU fill:#ffdddd,stroke:#cc0000
    style DT fill:#ffdddd,stroke:#cc0000
```
