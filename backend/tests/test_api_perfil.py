"""HU-03: actualización del perfil con PATCH /me."""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.dependencias import obtener_repositorio_usuarios
from app.main import app
from app.services.security import crear_access_token

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

    def actualizar(self, usuario_id: int, cambios: dict):
        if usuario_id != USUARIO["id"]:
            return None
        return {**USUARIO, **cambios}


@pytest.fixture
def cliente():
    app.dependency_overrides[obtener_repositorio_usuarios] = RepositorioEnMemoria
    yield TestClient(app)
    app.dependency_overrides.clear()


def encabezado() -> dict[str, str]:
    return {"Authorization": f"Bearer {crear_access_token('7')}"}


def test_actualiza_solo_los_campos_enviados(cliente):
    r = cliente.patch(
        "/me",
        headers=encabezado(),
        json={"nombre": "Ana María", "altura_cm": 170},
    )
    assert r.status_code == 200
    datos = r.json()
    assert datos["nombre"] == "Ana María"
    assert float(datos["altura_cm"]) == 170.0
    assert datos["correo"] == "ana@correo.com"


def test_sin_cambios_devuelve_el_perfil(cliente):
    r = cliente.patch("/me", headers=encabezado(), json={})
    assert r.status_code == 200
    assert r.json()["correo"] == "ana@correo.com"


def test_rechaza_campo_desconocido(cliente):
    r = cliente.patch(
        "/me",
        headers=encabezado(),
        json={"correo": "otra@correo.com"},
    )
    assert r.status_code == 422


def test_rechaza_menor_de_edad(cliente):
    r = cliente.patch(
        "/me",
        headers=encabezado(),
        json={"fecha_nacimiento": f"{datetime.now().year - 17}-01-01"},
    )
    assert r.status_code == 422
    assert "18 años" in r.json()["detail"]


def test_rechaza_altura_fuera_de_rango(cliente):
    r = cliente.patch(
        "/me",
        headers=encabezado(),
        json={"altura_cm": 90},
    )
    assert r.status_code == 422
    assert "100" in r.json()["detail"]


def test_sin_token(cliente):
    r = cliente.patch("/me", json={"nombre": "Ana"})
    assert r.status_code == 401
