from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencias import obtener_repositorio_usuarios, obtener_usuario_actual
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import UsuarioPublico
from app.schemas.perfil import PerfilUpdateRequest

router = APIRouter(tags=["Perfil"])


@router.get("/me", response_model=UsuarioPublico)
def obtener_perfil(usuario: dict[str, Any] = Depends(obtener_usuario_actual)) -> dict[str, Any]:
    """Datos del usuario con sesión iniciada."""
    return usuario


@router.patch("/me", response_model=UsuarioPublico)
def actualizar_perfil(
    datos: PerfilUpdateRequest,
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
    usuarios: UsuarioRepository = Depends(obtener_repositorio_usuarios),
) -> dict[str, Any]:
    """Actualiza el perfil. Los cambios aplican a los planes creados después."""
    cambios = datos.model_dump(exclude_unset=True, mode="json")
    if not cambios:
        return usuario

    actualizado = usuarios.actualizar(usuario["id"], cambios)
    if actualizado is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión no es válida. Inicia sesión de nuevo.",
        )
    return actualizado
