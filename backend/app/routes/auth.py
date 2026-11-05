from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencias import obtener_auth_service
from app.schemas.auth import LoginRequest, RegistroRequest, TokenResponse
from app.services.auth_service import AuthService, ErrorAutenticacion

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post(
    "/registro",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar(
    datos: RegistroRequest,
    auth_service: AuthService = Depends(obtener_auth_service),
) -> TokenResponse:
    perfil = datos.model_dump(
        mode="json",
        exclude={"correo", "contrasena"},
    )

    try:
        return auth_service.registrar(
            correo=str(datos.correo).strip().lower(),
            contrasena=datos.contrasena,
            perfil=perfil,
        )
    except ErrorAutenticacion as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=str(error),
        ) from error


@router.post("/login", response_model=TokenResponse)
def iniciar_sesion(
    datos: LoginRequest,
    auth_service: AuthService = Depends(obtener_auth_service),
) -> TokenResponse:
    try:
        return auth_service.iniciar_sesion(
            correo=str(datos.correo).strip().lower(),
            contrasena=datos.contrasena,
        )
    except ErrorAutenticacion as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=str(error),
        ) from error