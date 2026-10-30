from datetime import datetime, timedelta, timezone

import jwt
import bcrypt

from app.services.configuracion import configuraciones

_ALGORITMO_JWT = "HS256"

def hash_contrasena(contrasena: str) -> str:
    contrasena_bytes = contrasena.encode("utf-8")
    if len(contrasena_bytes) > 72:
        raise ValueError("La contraseña no puede tener más de 72 bytes.")
    return bcrypt.hashpw(contrasena_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")

def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    contrasena_bytes = contrasena.encode("utf-8")
    if len(contrasena_bytes) > 72:
        return False
    
    return bcrypt.checkpw(contrasena_bytes, hash_guardado.encode("utf-8"))

def crear_access_token(usuario_id: str) -> str:
    ahora = datetime.now(timezone.utc)
    expiracion = ahora + timedelta(minutes=configuraciones.jwt_expiration_minutes)
    payload = {
        "sub": usuario_id,
        "iat": ahora.timestamp(),
        "exp": expiracion.timestamp(),
    }
    return jwt.encode(payload, configuraciones.jwt_secret, algorithm=_ALGORITMO_JWT)