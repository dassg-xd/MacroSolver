from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencias import (
    obtener_repositorio_planes,
    obtener_usuario_actual,
)
from app.schemas.plan import (
    DatosPlanRequest,
    EstimarComposicionRequest,
    VistaPreviaResponse,
    PlanResponse,
    CalculoResponse,
)
from app.services.plan_service import (
    ErrorPlan,
    calculo_activo,
    crear_plan,
    estimar_composicion,
    obtener_activo,
    vista_previa,
)

router = APIRouter(prefix="/plans", tags=["Planes"])


def _http_error(error: ErrorPlan) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.mensaje)


@router.post("/estimar-composicion", response_model=dict)
def estimar(
    datos: EstimarComposicionRequest,
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
) -> dict[str, Any]:
    return estimar_composicion(usuario, datos)


@router.post("/preview", response_model=VistaPreviaResponse)
def preview(
    datos: DatosPlanRequest,
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
) -> dict[str, Any]:
    return vista_previa(usuario, datos)


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def crear(
    datos: DatosPlanRequest,
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
    repositorio: Any = Depends(obtener_repositorio_planes),
) -> dict[str, Any]:
    try:
        return crear_plan(usuario, datos, repositorio)
    except ErrorPlan as error:
        raise _http_error(error) from error


@router.get("/active/calculo", response_model=CalculoResponse)
def calcular(
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
    repositorio: Any = Depends(obtener_repositorio_planes),
) -> dict[str, Any]:
    try:
        return calculo_activo(usuario, repositorio)
    except ErrorPlan as error:
        raise _http_error(error) from error


@router.get("/active", response_model=PlanResponse)
def activo(
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
    repositorio: Any = Depends(obtener_repositorio_planes),
) -> dict[str, Any]:
    try:
        return obtener_activo(usuario, repositorio)
    except ErrorPlan as error:
        raise _http_error(error) from error
