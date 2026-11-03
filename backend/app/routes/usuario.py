from typing import Any

from fastapi import APIRouter, Depends

from app.dependencias import obtener_usuario_actual
from app.schemas.auth import UsuarioPublico

router = APIRouter(tags=["Perfil"])


@router.get("/me", response_model=UsuarioPublico)
def obtener_perfil(usuario: dict[str, Any] = Depends(obtener_usuario_actual)) -> dict[str, Any]:
    """Datos del usuario con sesión iniciada."""
    return usuario
