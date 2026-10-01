"""Los tests usan la base del .env, pero cada test corre dentro de una transacción
que se revierte al final: nunca quedan datos guardados."""
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from studyia.core.rate_limit import login_rate_limiter
from studyia.core.security import hash_password
from studyia.database.connection import engine, get_db
from studyia.main import app
from studyia.models import RoleName, User
from studyia.services.user_service import get_role_by_name

PASSWORD = "Clave12345"


@pytest.fixture
def db() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    # Los commit() del código se convierten en savepoints dentro de la transacción
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> Generator[None, None, None]:
    login_rate_limiter.clear()
    yield
    login_rate_limiter.clear()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_user(db: Session, email: str, role: RoleName = RoleName.ESTUDIANTE, **extra) -> User:
    user = User(
        name="Usuario Test",
        email=email,
        password=hash_password(PASSWORD),
        role=get_role_by_name(db, role),
        **extra,
    )
    db.add(user)
    db.commit()
    return user


def login(client: TestClient, email: str, password: str = PASSWORD) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def auth_header(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
