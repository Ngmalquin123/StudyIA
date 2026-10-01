"""Crea el primer administrador, o convierte en admin a un usuario existente.

Uso (desde backend/):
    uv run python -m studyia.create_admin
"""
from getpass import getpass

from studyia.core.security import hash_password
from studyia.database.connection import SessionLocal
from studyia.services.auth_service import ADMIN_ROLE, get_role_by_name, get_user_by_email
from studyia.models import User


def main() -> None:
    email = input("Email del admin: ").strip().lower()

    with SessionLocal() as db:
        admin_role = get_role_by_name(db, ADMIN_ROLE)
        user = get_user_by_email(db, email)

        if user is not None:
            user.role = admin_role
            db.commit()
            print(f"'{email}' ya existía: ahora es admin.")
            return

        name = input("Nombre: ").strip()
        password = getpass("Contraseña (mínimo 8 caracteres): ")
        if len(name) < 2 or len(password) < 8:
            print("Nombre o contraseña demasiado cortos. No se creó nada.")
            return
        if password != getpass("Repite la contraseña: "):
            print("Las contraseñas no coinciden. No se creó nada.")
            return

        db.add(User(name=name, email=email, password=hash_password(password), role=admin_role))
        db.commit()
        print(f"Admin '{email}' creado.")


if __name__ == "__main__":
    main()
