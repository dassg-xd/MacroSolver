"""Endpoints de planeación sin red."""
import os
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


def datos_preview(**cambios):
    base = {
        "peso_inicial_kg": 80,
        "peso_objetivo_kg": 75,
        "fecha_meta": (date.today() + timedelta(days=60)).isoformat(),
        "cuello_cm": 34,
        "cintura_cm": 90,
        "cadera_cm": 100,
    }
    base.update(cambios)
    return base


def test_sin_token():
    cliente = TestClient(app)
    assert cliente.post("/plans/preview", json=datos_preview()).status_code == 401
    assert cliente.get("/plans/active").status_code == 401


def test_preview_responde_200_con_bloqueos(cliente):
    r = cliente.post(
        "/plans/preview",
        headers=encabezado(),
        json=datos_preview(peso_objetivo_kg=85, peso_inicial_kg=80),
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["puede_confirmar"] is False
    assert any(b["codigo"] == "meta_no_es_perdida" for b in cuerpo["bloqueos"])


def test_preview_viable(cliente):
    r = cliente.post("/plans/preview", headers=encabezado(), json=datos_preview())
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["puede_confirmar"] is True
    assert cuerpo["ingesta_kcal"] is not None
    assert cuerpo["curva"] is not None
    assert len(cuerpo["curva"]["peso_kg"]) == 61


def test_preview_datos_invalidos_422(cliente):
    r = cliente.post(
        "/plans/preview",
        headers=encabezado(),
        json=datos_preview(fecha_meta=date.today().isoformat()),
    )
    assert r.status_code == 422


def test_crear_plan_201(cliente, repositorio):
    r = cliente.post("/plans", headers=encabezado(), json=datos_preview())
    assert r.status_code == 201
    assert r.json()["id"] == 42
    assert repositorio.activo is not None
    assert repositorio.activo["masa_libre_inicial_kg"] is not None


def test_preview_y_crear_plan_sin_medidas_opcionales(cliente, repositorio):
    datos = datos_preview()
    datos.pop("cuello_cm")
    datos.pop("cintura_cm")
    datos.pop("cadera_cm")

    previa = cliente.post("/plans/preview", headers=encabezado(), json=datos)
    assert previa.status_code == 200
    assert previa.json()["puede_confirmar"] is True
    assert previa.json()["composicion"]["metodo"] == "deurenberg"

    creado = cliente.post("/plans", headers=encabezado(), json=datos)
    assert creado.status_code == 201
    assert creado.json()["composicion"]["metodo"] == "deurenberg"
    assert repositorio.activo["cuello_cm"] is None
    assert repositorio.activo["cintura_cm"] is None


def test_crear_plan_bloqueado_422(cliente):
    r = cliente.post(
        "/plans",
        headers=encabezado(),
        json=datos_preview(peso_objetivo_kg=85, peso_inicial_kg=80),
    )
    assert r.status_code == 422


def test_activo_200(cliente, repositorio):
    cliente.post("/plans", headers=encabezado(), json=datos_preview())
    r = cliente.get("/plans/active", headers=encabezado())
    assert r.status_code == 200
    assert r.json()["id"] == 42


def test_activo_404(cliente):
    r = cliente.get("/plans/active", headers=encabezado())
    assert r.status_code == 404


def test_estimar_composicion(cliente):
    r = cliente.post(
        "/plans/estimar-composicion",
        headers=encabezado(),
        json={"peso_kg": 80, "cuello_cm": 34, "cintura_cm": 90, "cadera_cm": 100},
    )
    assert r.status_code == 200
    assert r.json()["metodo"] == "marina"
    assert r.json()["grasa_kg"] > 0


def test_preview_incluye_equivalente_en_grasa(cliente):
    r = cliente.post("/plans/preview", json=datos_preview(), headers=encabezado())
    eq = r.json()["equivalente_grasa"]
    assert eq["grasa_a_perder_kg"] == 5.0
    assert eq["peso_meta_kg"] < 75.0     # perder 5 kg de grasa exige bajar más de 5 kg
