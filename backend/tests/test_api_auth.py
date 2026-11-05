"""Pruebas de la API de sesión sin red: el repositorio de usuarios se reemplaza por uno en memoria."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.dependencias import obtener_auth_service, obtener_repositorio_usuarios
from app.main import app
from app.services.auth_service import AuthService, GestorIntentosFallidos
from app.services.configuracion import configuraciones
from app.services.security import crear_access_token, hash_contrasena

USUARIO = {
    "id": 7,
    "correo": "ana@correo.com",
    "nombre": "Ana",
    "sexo": "Femenino",
    "fecha_nacimiento": "1995-04-12",
    "altura_cm": "165.0",
    "factor_actividad": "1.55",
    "nivel_entrenamiento": "principiante",
    "creado_en": "2026-11-01T10:00:00+00:00",
}


class RepositorioEnMemoria:
    def buscar_por_id(self, usuario_id: int):
        return dict(USUARIO) if usuario_id == USUARIO["id"] else None


@pytest.fixture
def cliente():
    app.dependency_overrides[obtener_repositorio_usuarios] = RepositorioEnMemoria
    yield TestClient(app)
    app.dependency_overrides.clear()


def encabezado(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_me_devuelve_el_usuario(cliente):
    r = cliente.get("/me", headers=encabezado(crear_access_token("7")))
    assert r.status_code == 200
    datos = r.json()
    assert datos["correo"] == "ana@correo.com"
    assert "hash_contrasena" not in datos


def test_me_sin_token(cliente):
    r = cliente.get("/me")
    assert r.status_code == 401
    assert r.json()["detail"] == "Debes iniciar sesión."


def test_me_token_expirado(cliente):
    hace_un_dia = datetime.now(timezone.utc) - timedelta(days=1)
    token = jwt.encode({"sub": "7", "iat": hace_un_dia, "exp": hace_un_dia + timedelta(minutes=5)},
                       configuraciones.jwt_secret, algorithm="HS256")
    r = cliente.get("/me", headers=encabezado(token))
    assert r.status_code == 401
    assert "expiró" in r.json()["detail"]


def test_me_token_con_otra_firma(cliente):
    token = jwt.encode({"sub": "7", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                       "otro-secreto-de-mas-de-32-caracteres-xx", algorithm="HS256")
    r = cliente.get("/me", headers=encabezado(token))
    assert r.status_code == 401
    assert "no es válida" in r.json()["detail"]


def test_me_usuario_borrado(cliente):
    r = cliente.get("/me", headers=encabezado(crear_access_token("999")))
    assert r.status_code == 401


def test_login_bloquea_tras_tres_intentos_en_la_api():
    class RepositorioLogin:
        def buscar_por_correo(self, correo: str):
            return {
                **USUARIO,
                "hash_contrasena": hash_contrasena("clave123"),
            }

    servicio = AuthService(
        usuarios=RepositorioLogin(),
        intentos=GestorIntentosFallidos(),
    )
    app.dependency_overrides[obtener_auth_service] = lambda: servicio
    cliente = TestClient(app)
    try:
        for _ in range(2):
            r = cliente.post(
                "/auth/login",
                json={"correo": "ana@correo.com", "contrasena": "incorrecta1"},
            )
            assert r.status_code == 401
            assert r.json()["detail"] == "Correo o contraseña incorrectos."

        r = cliente.post(
            "/auth/login",
            json={"correo": "ana@correo.com", "contrasena": "incorrecta1"},
        )
        assert r.status_code == 429
        assert "15 minutos" in r.json()["detail"]
    finally:
        app.dependency_overrides.clear()
