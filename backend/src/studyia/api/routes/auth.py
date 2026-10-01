from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from studyia.api.deps import CurrentUser, DbSession
from studyia.core.security import create_access_token
from studyia.schemas.auth import LoginRequest, LoginResponse, Token
from studyia.schemas.user import UserCreate, UserRead
from studyia.services import auth_service


router = APIRouter(prefix="/auth", tags=["Autenticación"])

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Email o contraseña incorrectos",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession):
    try:
        user = auth_service.register_user(db, data)
    except auth_service.EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )
    return auth_service.to_user_read(user)


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: DbSession):
    """Login para el frontend: recibe JSON y devuelve el token + datos del usuario."""
    user = auth_service.authenticate(db, data.email, data.password)
    if user is None:
        raise INVALID_CREDENTIALS
    token = create_access_token(user.id)
    return LoginResponse(access_token=token, user=auth_service.to_user_read(user))


@router.post("/token", response_model=Token, include_in_schema=False)
def token(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    """Login con formulario OAuth2; lo usa el botón 'Authorize' de Swagger (/docs)."""
    user = auth_service.authenticate(db, form.username, form.password)
    if user is None:
        raise INVALID_CREDENTIALS
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser):
    return auth_service.to_user_read(current_user)
