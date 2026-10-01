from studyia.core.security import create_access_token, create_refresh_token
from tests.conftest import PASSWORD, auth_header, login, make_user

EMAIL = "test.auth@pruebas-studyia.com"


def test_register_login_and_me(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Ana", "email": "Ana.Test@Pruebas-StudyIA.com", "password": PASSWORD},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "ana.test@pruebas-studyia.com"
    assert response.json()["rol"] == "estudiante"

    tokens = login(client, "ANA.TEST@pruebas-studyia.com")
    assert tokens["token_type"] == "bearer"
    assert tokens["refresh_token"]
    assert tokens["user"]["email"] == "ana.test@pruebas-studyia.com"

    me = client.get("/api/auth/me", headers=auth_header(tokens))
    assert me.status_code == 200
    assert me.json()["id"] == tokens["user"]["id"]


def test_register_duplicate_email(client, db):
    make_user(db, EMAIL)
    response = client.post(
        "/api/auth/register", json={"name": "Otro", "email": EMAIL, "password": PASSWORD}
    )
    assert response.status_code == 409


def test_register_validates_input(client):
    response = client.post(
        "/api/auth/register", json={"name": "A", "email": "no-es-email", "password": "123"}
    )
    assert response.status_code == 422


def test_login_wrong_password_and_unknown_email_same_error(client, db):
    make_user(db, EMAIL)
    wrong = client.post("/api/auth/login", json={"email": EMAIL, "password": "incorrecta"})
    unknown = client.post(
        "/api/auth/login", json={"email": "nadie@pruebas-studyia.com", "password": PASSWORD}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_inactive_user_cannot_login_nor_use_token(client, db):
    user = make_user(db, EMAIL)
    tokens = login(client, EMAIL)
    user.is_active = False
    db.commit()

    assert client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD}).status_code == 401
    assert client.get("/api/auth/me", headers=auth_header(tokens)).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer basura"}).status_code == 401


def test_refresh_returns_new_tokens(client, db):
    make_user(db, EMAIL)
    tokens = login(client, EMAIL)
    response = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    assert client.get("/api/auth/me", headers=auth_header(response.json())).status_code == 200


def test_token_types_are_not_interchangeable(client, db):
    user = make_user(db, EMAIL)
    refresh = create_refresh_token(user.id)
    access = create_access_token(user.id)
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {refresh}"}).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": access}).status_code == 401


def test_swagger_token_endpoint(client, db):
    make_user(db, EMAIL)
    response = client.post("/api/auth/token", data={"username": EMAIL, "password": PASSWORD})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_blocked_after_too_many_failures(client, db):
    from studyia.core.rate_limit import login_rate_limiter

    make_user(db, EMAIL)
    for _ in range(login_rate_limiter.max_attempts):
        assert client.post("/api/auth/login", json={"email": EMAIL, "password": "mala"}).status_code == 401

    blocked = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


def test_successful_login_resets_failures(client, db):
    from studyia.core.rate_limit import login_rate_limiter

    make_user(db, EMAIL)
    for _ in range(login_rate_limiter.max_attempts - 1):
        client.post("/api/auth/login", json={"email": EMAIL, "password": "mala"})
    login(client, EMAIL)
    assert client.post("/api/auth/login", json={"email": EMAIL, "password": "mala"}).status_code == 401
