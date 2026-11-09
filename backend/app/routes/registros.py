from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencias import (
    obtener_repositorio_planes,
    obtener_repositorio_registros,
    obtener_usuario_actual,
)
from app.schemas.registro import (
    ActividadCatalogo,
    ActividadesRequest,
    ActividadesResponse,
    CalendarioResponse,
    CaloriasRequest,
    CaloriasResponse,
    PesoRequest,
    PesoResponse,
)
from app.services import registro_service
from app.services.plan_service import ErrorPlan

router = APIRouter(tags=["Registros"])


def _http_error(error: ErrorPlan) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.mensaje)


@router.get("/actividades", response_model=list[ActividadCatalogo])
def catalogo(
    _: dict[str, Any] = Depends(obtener_usuario_actual),
    registros: Any = Depends(obtener_repositorio_registros),
) -> list[dict[str, Any]]:
    """Catálogo de actividades físicas con su MET."""
    return registro_service.catalogo_actividades(registros)


@router.get("/plans/active/calendario", response_model=CalendarioResponse)
def calendario(
    mes: str | None = Query(default=None, description="Mes en formato AAAA-MM; por defecto, el actual."),
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
    planes: Any = Depends(obtener_repositorio_planes),
    registros: Any = Depends(obtener_repositorio_registros),
) -> dict[str, Any]:
    try:
        return registro_service.calendario(usuario, mes, planes, registros)
    except ErrorPlan as error:
        raise _http_error(error) from error


@router.put("/plans/active/calorias", response_model=CaloriasResponse)
def calorias(
    datos: CaloriasRequest,
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
    planes: Any = Depends(obtener_repositorio_planes),
    registros: Any = Depends(obtener_repositorio_registros),
) -> dict[str, Any]:
    try:
        return registro_service.guardar_calorias(usuario, datos, planes, registros)
    except ErrorPlan as error:
        raise _http_error(error) from error


@router.put("/plans/active/pesos", response_model=PesoResponse)
def pesos(
    datos: PesoRequest,
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
    planes: Any = Depends(obtener_repositorio_planes),
    registros: Any = Depends(obtener_repositorio_registros),
) -> dict[str, Any]:
    try:
        return registro_service.guardar_peso(usuario, datos, planes, registros)
    except ErrorPlan as error:
        raise _http_error(error) from error


@router.put("/plans/active/actividades", response_model=ActividadesResponse)
def actividades(
    datos: ActividadesRequest,
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
    planes: Any = Depends(obtener_repositorio_planes),
    registros: Any = Depends(obtener_repositorio_registros),
) -> dict[str, Any]:
    try:
        return registro_service.guardar_actividades(usuario, datos, planes, registros)
    except ErrorPlan as error:
        raise _http_error(error) from error
