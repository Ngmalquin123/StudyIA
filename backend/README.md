# StudyIA - Backend

API en FastAPI + SQLAlchemy 2 + PostgreSQL, con migraciones en Alembic y login con JWT.

## Estructura

```
src/studyia/
  main.py              App FastAPI (CORS, routers, /health)
  core/config.py       Variables de entorno (.env)
  core/security.py     Hash de contraseñas (argon2) y JWT
  database/            Base declarativa, engine y sesión (get_db)
  models/              Modelos SQLAlchemy (una tabla por archivo)
  schemas/             Modelos Pydantic de entrada/salida
  services/            Lógica de negocio
  api/deps.py          Dependencias (sesión, usuario actual)
  api/routes/          Endpoints
migrations/            Migraciones Alembic
```

## Puesta en marcha

Todos los comandos se ejecutan desde `backend/`.

```bash
cp .env.example .env         # y completar los valores
uv sync                      # instalar dependencias
uv run alembic upgrade head  # crear/actualizar las tablas
uv run fastapi dev src/studyia/main.py
```

Documentación interactiva: http://localhost:8000/docs

## Endpoints de autenticación

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/auth/register` | Crea una cuenta (`name`, `email`, `password`); rol `estudiante` |
| POST | `/api/auth/login` | JSON `{email, password}` → `{access_token, token_type, user}` |
| GET | `/api/auth/me` | Usuario actual; requiere `Authorization: Bearer <token>` |

## Migraciones

```bash
# Después de cambiar o agregar un modelo (e importarlo en models/__init__.py)
uv run alembic revision --autogenerate -m "descripcion del cambio"
# Leer SIEMPRE el archivo generado antes de aplicarlo
uv run alembic upgrade head
uv run alembic downgrade -1   # deshacer la última
```
