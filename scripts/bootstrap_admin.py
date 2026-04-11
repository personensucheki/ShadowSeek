# scripts/bootstrap_admin.py
"""
Idempotentes Script zum Anlegen oder Aktualisieren des Bootstrap-Admins.
"""
from app.extensions import db
from app.models.user import User

def create_or_update_admin():
    username = "ADMIN"
    email = "personensucheki@gmail.com"
    password = "BitteSicheresPasswortSetzen!"  # TODO: Sicheren Wert setzen
    role = "super_admin"
    is_active = True

    user = User.query.filter_by(email=email).first()
    if user:
        updated = False
        if user.role != role:
            user.role = role
            updated = True
        if not user.is_active:
            user.is_active = True
            updated = True
        if updated:
            print(f"Admin-User aktualisiert: {user.email}")
        else:
            print(f"Admin-User existiert bereits und ist korrekt gesetzt: {user.email}")
    else:
        user = User(username=username, email=email, role=role, is_active=is_active)
        user.set_password(password)
        db.session.add(user)
        print(f"Admin-User neu angelegt: {user.email}")
    db.session.commit()

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        create_or_update_admin()
