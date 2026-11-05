"""HU-02B: bloqueo temporal tras tres intentos fallidos."""
from datetime import datetime, timedelta, timezone

import pytest

from app.services.auth_service import (
    AuthService,
    ErrorAutenticacion,
    GestorIntentosFallidos,
)
from app.services.security import hash_contrasena

AHORA = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


class RelojFijo:
    def __init__(self) -> None:
        self.ahora = AHORA

    def __call__(self) -> datetime:
        return self.ahora

    def avanzar(self, **cambios) -> None:
        self.ahora += timedelta(**cambios)


class RepositorioEnMemoria:
    def __init__(self, existe: bool = True) -> None:
        self.usuario = (
            {
                "id": 7,
                "correo": "ana@correo.com",
                "nombre": "Ana",
                "sexo": "Femenino",
                "fecha_nacimiento": "1995-04-12",
                "altura_cm": "165.0",
                "factor_actividad": "1.55",
                "nivel_entrenamiento": "principiante",
                "creado_en": "2026-11-01T10:00:00+00:00",
                "hash_contrasena": hash_contrasena("clave123"),
            }
            if existe
            else None
        )

    def buscar_por_correo(self, correo: str):
        if self.usuario is None:
            return None
        return dict(self.usuario) if correo == self.usuario["correo"] else None


def servicio(existe: bool = True):
    reloj = RelojFijo()
    auth = AuthService(
        usuarios=RepositorioEnMemoria(existe),
        intentos=GestorIntentosFallidos(reloj=reloj),
    )
    return auth, reloj


def test_tres_fallos_bloquean_quince_minutos():
    auth, _ = servicio()

    for _ in range(2):
        with pytest.raises(ErrorAutenticacion) as error:
            auth.iniciar_sesion("ana@correo.com", "incorrecta1")
        assert error.value.status_code == 401

    with pytest.raises(ErrorAutenticacion) as error:
        auth.iniciar_sesion("ana@correo.com", "incorrecta1")
    assert error.value.status_code == 429
    assert "15 minutos" in str(error.value)


def test_bloqueo_ignora_la_contrasena_correcta():
    auth, _ = servicio()
    for _ in range(3):
        with pytest.raises(ErrorAutenticacion):
            auth.iniciar_sesion("ana@correo.com", "incorrecta1")

    with pytest.raises(ErrorAutenticacion) as error:
        auth.iniciar_sesion("ana@correo.com", "clave123")
    assert error.value.status_code == 429


def test_bloqueo_expira():
    auth, reloj = servicio()
    for _ in range(3):
        with pytest.raises(ErrorAutenticacion):
            auth.iniciar_sesion("ana@correo.com", "incorrecta1")

    reloj.avanzar(minutes=15, seconds=1)
    respuesta = auth.iniciar_sesion("ana@correo.com", "clave123")
    assert respuesta["usuario"]["correo"] == "ana@correo.com"


def test_un_login_correcto_limpia_los_fallos():
    auth, _ = servicio()
    for _ in range(2):
        with pytest.raises(ErrorAutenticacion):
            auth.iniciar_sesion("ana@correo.com", "incorrecta1")

    auth.iniciar_sesion("ana@correo.com", "clave123")

    for _ in range(2):
        with pytest.raises(ErrorAutenticacion) as error:
            auth.iniciar_sesion("ana@correo.com", "incorrecta1")
        assert error.value.status_code == 401


def test_correo_inexistente_tambien_se_bloquea():
    auth, _ = servicio(existe=False)
    for _ in range(3):
        with pytest.raises(ErrorAutenticacion) as error:
            auth.iniciar_sesion("nadie@correo.com", "incorrecta1")
    assert error.value.status_code == 429
