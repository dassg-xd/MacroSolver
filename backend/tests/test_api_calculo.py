"""Endpoint /plans/active/calculo (HU-09)."""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.dependencias import obtener_repositorio_planes, obtener_repositorio_usuarios
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


class RepositorioUsuarios:
    def buscar_por_id(self, usuario_id: int):
        return dict(USUARIO) if usuario_id == USUARIO["id"] else None


class RepositorioPlanes:
    def __init__(self) -> None:
        self.activo = None

    def buscar_activo(self, usuario_id: int):
        return self.activo

    def crear(self, usuario_id: int, plan: dict):
        fila = {"id": 42, "estado": "activo", "creado_en": "2026-11-05T10:00:00+00:00", **plan}
        self.activo = fila
        return fila


@pytest.fixture
def repositorio():
    return RepositorioPlanes()


@pytest.fixture
def cliente(repositorio):
    app.dependency_overrides[obtener_repositorio_usuarios] = RepositorioUsuarios
    app.dependency_overrides[obtener_repositorio_planes] = lambda: repositorio
    yield TestClient(app)
    app.dependency_overrides.clear()


def encabezado():
    return {"Authorization": f"Bearer {crear_access_token('7')}"}


def datos_preview():
    return {
        "peso_inicial_kg": 80,
        "peso_objetivo_kg": 75,
        "fecha_meta": (date.today() + timedelta(days=60)).isoformat(),
        "cuello_cm": 34,
        "cintura_cm": 90,
        "cadera_cm": 100,
    }


def test_calculo_404_sin_plan(cliente):
    r = cliente.get("/plans/active/calculo", headers=encabezado())
    assert r.status_code == 404


def test_calculo_200_con_plan(cliente):
    cliente.post("/plans", headers=encabezado(), json=datos_preview())
    r = cliente.get("/plans/active/calculo", headers=encabezado())
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["secante"]["raiz_kcal"] is not None
    assert len(cuerpo["secante"]["iteraciones"]) > 0
    assert cuerpo["euler"]["error_maximo_kg"] is not None
    assert cuerpo["formulas"]["secante"]
    assert cuerpo["sensibilidad"] is not None
    assert cuerpo["composicion"]["metodo"] == "marina"
