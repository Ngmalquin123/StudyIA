from studyia.models import RoleName
from tests.conftest import PASSWORD, auth_header, login, make_user

ALUMNO = "alumno@pruebas-studyia.com"
OTRO = "otro@pruebas-studyia.com"
ADMIN = "admin.test@pruebas-studyia.com"


def test_student_cannot_list_users(client, db):
    make_user(db, ALUMNO)
    tokens = login(client, ALUMNO)
    assert client.get("/api/users", headers=auth_header(tokens)).status_code == 403


def test_admin_lists_users(client, db):
    make_user(db, ADMIN, RoleName.ADMIN)
    tokens = login(client, ADMIN)
    response = client.get("/api/users", headers=auth_header(tokens))
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_student_cannot_edit_other_user(client, db):
    make_user(db, ALUMNO)
    otro = make_user(db, OTRO)
    tokens = login(client, ALUMNO)
    response = client.patch(f"/api/users/{otro.id}", json={"name": "Hack"}, headers=auth_header(tokens))
    assert response.status_code == 403


def test_change_own_password_requires_current(client, db):
    user = make_user(db, ALUMNO)
    headers = auth_header(login(client, ALUMNO))
    url = f"/api/users/{user.id}"

    assert client.patch(url, json={"password": "NuevaClave1"}, headers=headers).status_code == 400
    assert client.patch(
        url, json={"password": "NuevaClave1", "current_password": "mala"}, headers=headers
    ).status_code == 400
    assert client.patch(
        url, json={"password": "NuevaClave1", "current_password": PASSWORD}, headers=headers
    ).status_code == 200
    login(client, ALUMNO, "NuevaClave1")


def test_student_cannot_change_role_or_activate(client, db):
    user = make_user(db, ALUMNO)
    headers = auth_header(login(client, ALUMNO))
    assert client.patch(f"/api/users/{user.id}", json={"rol": "admin"}, headers=headers).status_code == 403
    assert client.patch(f"/api/users/{user.id}", json={"is_active": False}, headers=headers).status_code == 403


def test_admin_deactivates_user(client, db):
    make_user(db, ADMIN, RoleName.ADMIN)
    alumno = make_user(db, ALUMNO)
    headers = auth_header(login(client, ADMIN))
    response = client.patch(f"/api/users/{alumno.id}", json={"is_active": False}, headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert client.post("/api/auth/login", json={"email": ALUMNO, "password": PASSWORD}).status_code == 401


def test_admin_cannot_demote_or_delete_self(client, db):
    admin = make_user(db, ADMIN, RoleName.ADMIN)
    headers = auth_header(login(client, ADMIN))
    assert client.patch(f"/api/users/{admin.id}", json={"rol": "estudiante"}, headers=headers).status_code == 400
    assert client.delete(f"/api/users/{admin.id}", headers=headers).status_code == 400


def test_student_deletes_own_account(client, db):
    user = make_user(db, ALUMNO)
    headers = auth_header(login(client, ALUMNO))
    assert client.delete(f"/api/users/{user.id}", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401
