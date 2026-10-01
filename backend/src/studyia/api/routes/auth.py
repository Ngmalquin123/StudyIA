from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from studyia.api.deps import CurrentUser, DbSession
from studyia.core.exceptions import EmailAlreadyRegistered
from studyia.core.rate_limit import login_rate_limiter
from studyia.models import User
from studyia.schemas.auth import LoginRequest, LoginResponse, RefreshRequest, Token
from studyia.schemas.user import UserCreate, UserRead
from studyia.services import auth_service


router = APIRouter(prefix="/auth", tags=["Autenticación"])

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Email o contraseña incorrectos",
    headers={"WWW-Authenticate": "Bearer"},
)


def authenticate_limited(request: Request, db: DbSession, email: str, password: str) -> User:
    """Login con límite de intentos fallidos por email + IP."""
    client_ip = request.client.host if request.client else "desconocida"
    key = f"{email.lower()}|{client_ip}"

    retry_after = login_rate_limiter.retry_after(key)
    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Intenta de nuevo más tarde",
            headers={"Retry-After": str(retry_after)},
        )

    user = auth_service.authenticate(db, email, password)
    if user is None:
        login_rate_limiter.register_failure(key)
        raise INVALID_CREDENTIALS
    login_rate_limiter.reset(key)
    return user


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession):
    try:
        user = auth_service.register_user(db, data)
    except EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )
    return UserRead.from_user(user)


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, request: Request, db: DbSession):
    """Login para el frontend: recibe JSON y devuelve los tokens + datos del usuario."""
    user = authenticate_limited(request, db, data.email, data.password)
    tokens = auth_service.issue_tokens(user)
    return LoginResponse(**tokens.model_dump(), user=UserRead.from_user(user))


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshRequest, db: DbSession):
    """Cambia un refresh token válido por un par de tokens nuevo.

    El frontend lo llama cuando el access token expira (respuesta 401),
    así la sesión sigue abierta sin volver a pedir la contraseña.
    """
    user = auth_service.get_active_user_from_token(db, data.refresh_token, "refresh")
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada, inicia sesión de nuevo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_service.issue_tokens(user)


@router.post("/token", response_model=Token, include_in_schema=False)
def token(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request, db: DbSession
):
    """Login con formulario OAuth2; lo usa el botón 'Authorize' de Swagger (/docs)."""
    user = authenticate_limited(request, db, form.username, form.password)
    return auth_service.issue_tokens(user)


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser):
    return UserRead.from_user(current_user)
