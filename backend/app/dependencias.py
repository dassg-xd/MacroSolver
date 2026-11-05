"""Dependencias compartidas por las rutas que requieren sesión."""
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import AuthService
from app.services.security import (
    TokenExpiradoError,
    TokenInvalidoError,
    decodificar_access_token,
)

_esquema_bearer = HTTPBearer(auto_error=False)

# Una sola instancia para que el bloqueo de intentos (HU-02B) sobreviva
# entre peticiones del mismo proceso.
_auth_service = AuthService()


def obtener_repositorio_usuarios() -> UsuarioRepository:
    return UsuarioRepository()


def obtener_auth_service() -> AuthService:
    return _auth_service


def _no_autorizado(mensaje: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=mensaje,
        headers={"WWW-Authenticate": "Bearer"},
    )


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
    usuarios: UsuarioRepository = Depends(obtener_repositorio_usuarios),
) -> dict[str, Any]:
    """Lee el JWT del encabezado Authorization y devuelve el usuario (sin hash)."""
    if credenciales is None or credenciales.scheme.lower() != "bearer":
        raise _no_autorizado("Debes iniciar sesión.")

    try:
        usuario_id = decodificar_access_token(credenciales.credentials)
    except TokenExpiradoError as error:
        raise _no_autorizado("Tu sesión expiró. Inicia sesión de nuevo.") from error
    except TokenInvalidoError as error:
        raise _no_autorizado("La sesión no es válida. Inicia sesión de nuevo.") from error

    usuario = usuarios.buscar_por_id(usuario_id)
    if usuario is None:
        raise _no_autorizado("La sesión no es válida. Inicia sesión de nuevo.")
    return usuario
