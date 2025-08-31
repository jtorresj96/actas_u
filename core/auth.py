from repositories.users import fetch_user
from core.security import check_password

def authenticate(username: str, password: str):
    u = fetch_user(username)
    if not u or not u["active"]:
        return False, "Usuario inválido o inactivo."
    if not check_password(password, u["password_hash"]):
        return False, "Usuario o contraseña incorrectos."
    return True, u