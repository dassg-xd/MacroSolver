from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencias import (
    obtener_repositorio_planes,
    obtener_repositorio_registros,
    obtener_usuario_actual,
)
from app.schemas.plan import PlanResponse
from app.schemas.seguimiento import (
    EstadisticasResponse,
    GuiaResponse,
    PlanHistorial,
    ReplaneacionPreviaResponse,
    ReplanearRequest,
    SeguimientoResponse,
)
from app.services import seguimiento_service
from app.services.plan_service import ErrorPlan

router = APIRouter(tags=["Seguimiento"])


def _http_error(error: ErrorPlan) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.mensaje)


@router.get("/plans/active/seguimiento", response_model=SeguimientoResponse)
def seguimiento(
    usuario: dict[str, Any] = Depends(obtener_usuario_actual),
    planes: Any = Depends(obtener_repositorio_planes),
    registros: Any = Depends(obtener_repositorio_registros),
) -> dict[str, Any]:
    try:
        return seguimiento_service.seguimiento(usuario, planes, registros)
    except ErrorPlan as error:
        raise _http_error(error) from error
