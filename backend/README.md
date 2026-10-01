# StudyIA - Backend

API en FastAPI + SQLAlchemy 2 + PostgreSQL, con migraciones en Alembic y login con JWT.

## Estructura

```
src/studyia/
  main.py              App FastAPI (CORS, routers, /health)
  core/config.py       Variables de entorno (.env)
  core/security.py     Hash de contraseñas (argon2) y JWT (access + refresh)
  core/exceptions.py   Errores de negocio (los servicios los lanzan, las rutas los traducen a HTTP)
  database/            Base declarativa, engine y sesión (get_db)
  models/              Modelos SQLAlchemy (una tabla por archivo)
  schemas/             Modelos Pydantic de entrada/salida
  services/            Lógica de negocio (auth_service: login/tokens, user_service: usuarios y roles)
  api/deps.py          Dependencias (sesión, usuario actual)
  api/routes/          Endpoints
migrations/            Migraciones Alembic
tests/                 Tests con pytest
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
| POST | `/api/auth/login` | JSON `{email, password}` → `{access_token, refresh_token, token_type, user}` |
| POST | `/api/auth/refresh` | JSON `{refresh_token}` → par de tokens nuevo |
| GET | `/api/auth/me` | Usuario actual; requiere `Authorization: Bearer <token>` |

### Cómo funciona la sesión

1. El login devuelve dos tokens:
   - `access_token` (30 min): se envía en cada petición como `Authorization: Bearer <token>`.
   - `refresh_token` (7 días): solo sirve para `POST /api/auth/refresh`.
2. Cuando una petición responde `401`, el frontend llama a `/api/auth/refresh`; si también da `401`, manda al usuario al login.
3. Cerrar sesión = borrar los dos tokens del navegador (los JWT no se guardan en el servidor).
4. Una cuenta con `is_active = false` no puede iniciar sesión y sus tokens dejan de funcionar.
5. Tras 5 intentos fallidos con el mismo email desde la misma IP, el login responde `429` durante 15 minutos (configurable en `.env`). El contador vive en memoria: se reinicia al reiniciar la API.

Reglas de `PATCH /api/users/{id}`: para cambiar la contraseña propia hay que enviar `current_password`; `rol` e `is_active` solo los cambia un admin y nunca sobre su propia cuenta.

## Tests

```bash
uv run pytest
```

Usan la base del `.env`, pero cada test corre dentro de una transacción que se revierte: no dejan datos.

## Migraciones

```bash
# Después de cambiar o agregar un modelo (e importarlo en models/__init__.py)
uv run alembic revision --autogenerate -m "descripcion del cambio"
# Leer SIEMPRE el archivo generado antes de aplicarlo
uv run alembic upgrade head
uv run alembic downgrade -1   # deshacer la última
```
