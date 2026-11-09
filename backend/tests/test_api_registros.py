"""Registros diarios y calendario sin red: planes y registros viven en memoria."""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.dependencias import (
    obtener_repositorio_planes,
    obtener_repositorio_registros,
    obtener_repositorio_usuarios,
)
from app.main import app
from app.services import registro_service
from app.services.security import crear_access_token

HOY = date(2026, 11, 20)
INICIO = date(2026, 11, 10)

USUARIO = {
    "id": 7, "correo": "ana@correo.com", "nombre": "Ana", "sexo": "Femenino",
    "fecha_nacimiento": "1995-04-12", "altura_cm": "165.0", "factor_actividad": "1.55",
    "nivel_entrenamiento": "principiante", "creado_en": "2026-11-01T10:00:00+00:00",
}
PLAN = {
    "id": 42, "usuario_id": 7, "fecha_inicio": INICIO.isoformat(), "plazo_dias": 60,
    "peso_inicial_kg": 80.0, "ingesta_kcal": 2000.0, "estado": "activo",
}
CATALOGO = [
    {"id": 1, "nombre": "Caminata", "tipo": "aerobico", "met": 3.5},
    {"id": 5, "nombre": "Pesas", "tipo": "fuerza", "met": 5.0},
]


class Usuarios:
    def buscar_por_id(self, usuario_id):
        return dict(USUARIO) if usuario_id == 7 else None


class Planes:
    def __init__(self, activo=True):
        self.activo = dict(PLAN) if activo else None

    def buscar_activo(self, usuario_id):
        return self.activo


class Registros:
    def __init__(self):
        self.calorias: dict[date, float] = {}
        self.pesos: dict[date, float] = {}
        self.actividades: dict[date, list[dict]] = {}

    def catalogo(self):
        return [dict(a) for a in CATALOGO]

    def listar(self, plan_id, desde, hasta):
        dentro = lambda d: desde <= d <= hasta
        return {
            "calorias": [{"fecha": d.isoformat(), "kcal": k} for d, k in sorted(self.calorias.items()) if dentro(d)],
            "pesos": [{"fecha": d.isoformat(), "peso_kg": p} for d, p in sorted(self.pesos.items()) if dentro(d)],
            "actividades": [
                {"fecha": d.isoformat(), **a}
                for d, lista in sorted(self.actividades.items()) if dentro(d) for a in lista
            ],
        }

    def ultimo_peso_hasta(self, plan_id, fecha):
        previos = [d for d in self.pesos if d <= fecha]
        return self.pesos[max(previos)] if previos else None

    def guardar_calorias(self, plan_id, fecha, kcal):
        self.calorias[fecha] = kcal

    def borrar_calorias(self, plan_id, fecha):
        self.calorias.pop(fecha, None)

    def guardar_peso(self, plan_id, fecha, peso_kg):
        self.pesos[fecha] = peso_kg

    def borrar_peso(self, plan_id, fecha):
        self.pesos.pop(fecha, None)

    def reemplazar_actividades(self, plan_id, fecha, actividades):
        if actividades:
            self.actividades[fecha] = [dict(a) for a in actividades]
        else:
            self.actividades.pop(fecha, None)


@pytest.fixture
def registros():
    return Registros()


@pytest.fixture
def planes():
    return Planes()


@pytest.fixture
def cliente(planes, registros, monkeypatch):
    monkeypatch.setattr(registro_service, "hoy", lambda: HOY)
    app.dependency_overrides[obtener_repositorio_usuarios] = Usuarios
    app.dependency_overrides[obtener_repositorio_planes] = lambda: planes
    app.dependency_overrides[obtener_repositorio_registros] = lambda: registros
    c = TestClient(app, headers={"Authorization": f"Bearer {crear_access_token('7')}"})
    yield c
    app.dependency_overrides.clear()


def dia(calendario, fecha):
    return next(d for d in calendario["dias"] if d["fecha"] == fecha.isoformat())


# ----------------------------------------------------------------- sesión y plan
def test_sin_token():
    c = TestClient(app)
    assert c.get("/plans/active/calendario").status_code == 401
    assert c.put("/plans/active/calorias", json={"fecha": "2026-11-12", "kcal": 1900}).status_code == 401


def test_sin_plan_activo_404(cliente, planes):
    planes.activo = None
    r = cliente.put("/plans/active/calorias", json={"fecha": "2026-11-12", "kcal": 1900})
    assert r.status_code == 404
    assert "plan activo" in r.json()["detail"]


# ----------------------------------------------------------------- calorías
def test_guardar_editar_y_borrar_calorias(cliente, registros):
    r = cliente.put("/plans/active/calorias", json={"fecha": "2026-11-12", "kcal": 1950})
    assert r.status_code == 200 and r.json() == {"fecha": "2026-11-12", "kcal": 1950.0}
    cliente.put("/plans/active/calorias", json={"fecha": "2026-11-12", "kcal": 2100})
    assert registros.calorias[date(2026, 11, 12)] == 2100.0
    cliente.put("/plans/active/calorias", json={"fecha": "2026-11-12", "kcal": None})
    assert date(2026, 11, 12) not in registros.calorias


@pytest.mark.parametrize("fecha,codigo_texto", [
    ("2026-11-09", "empezó"),       # antes del plan
    ("2026-11-21", "futuros"),      # mañana
])
def test_fecha_fuera_de_rango(cliente, fecha, codigo_texto):
    r = cliente.put("/plans/active/calorias", json={"fecha": fecha, "kcal": 1900})
    assert r.status_code == 422
    assert codigo_texto in r.json()["detail"]


def test_hoy_y_el_dia_de_inicio_se_aceptan(cliente):
    assert cliente.put("/plans/active/calorias", json={"fecha": HOY.isoformat(), "kcal": 1900}).status_code == 200
    assert cliente.put("/plans/active/calorias", json={"fecha": INICIO.isoformat(), "kcal": 1900}).status_code == 200


def test_kcal_negativas_422(cliente):
    r = cliente.put("/plans/active/calorias", json={"fecha": "2026-11-12", "kcal": -5})
    assert r.status_code == 422


# ----------------------------------------------------------------- peso
def test_guardar_peso(cliente, registros):
    r = cliente.put("/plans/active/pesos", json={"fecha": "2026-11-15", "peso_kg": 79.4})
    assert r.status_code == 200
    assert registros.pesos[date(2026, 11, 15)] == 79.4


def test_peso_del_dia_de_inicio_es_fijo(cliente):
    r = cliente.put("/plans/active/pesos", json={"fecha": INICIO.isoformat(), "peso_kg": 79})
    assert r.status_code == 422
    assert "peso inicial" in r.json()["detail"]


def test_peso_fuera_de_rango(cliente):
    assert cliente.put("/plans/active/pesos", json={"fecha": "2026-11-15", "peso_kg": 10}).status_code == 422


# ----------------------------------------------------------------- actividades
def test_actividades_reemplazan_el_dia(cliente, registros):
    r = cliente.put("/plans/active/actividades", json={
        "fecha": "2026-11-14",
        "actividades": [{"actividad_id": 1, "minutos": 60}, {"actividad_id": 5, "minutos": 30}],
    })
    assert r.status_code == 200
    cuerpo = r.json()
    # 80 kg · (2,5 · 1 h + 4 · 0,5 h) = 360 kcal
    assert cuerpo["kcal_ejercicio"] == pytest.approx(360.0)
    assert [a["nombre"] for a in cuerpo["actividades"]] == ["Caminata", "Pesas"]

    cliente.put("/plans/active/actividades", json={"fecha": "2026-11-14", "actividades": []})
    assert date(2026, 11, 14) not in registros.actividades


def test_actividad_inexistente(cliente):
    r = cliente.put("/plans/active/actividades", json={
        "fecha": "2026-11-14", "actividades": [{"actividad_id": 99, "minutos": 20}]})
    assert r.status_code == 422
    assert "catálogo" in r.json()["detail"]


def test_minutos_invalidos(cliente):
    r = cliente.put("/plans/active/actividades", json={
        "fecha": "2026-11-14", "actividades": [{"actividad_id": 1, "minutos": 0}]})
    assert r.status_code == 422


def test_catalogo(cliente):
    r = cliente.get("/actividades")
    assert r.status_code == 200
    assert r.json()[0] == {"id": 1, "nombre": "Caminata", "tipo": "aerobico", "met": 3.5}


# ----------------------------------------------------------------- calendario
def test_calendario_del_mes(cliente, registros):
    registros.calorias[date(2026, 11, 12)] = 2150.0   # dentro de ±10 %
    registros.calorias[date(2026, 11, 13)] = 2500.0   # fuera
    registros.pesos[date(2026, 11, 13)] = 79.0
    registros.actividades[date(2026, 11, 14)] = [{"actividad_id": 5, "minutos": 60}]

    r = cliente.get("/plans/active/calendario", params={"mes": "2026-11"})
    assert r.status_code == 200
    cal = r.json()
    assert cal["mes"] == "2026-11" and len(cal["dias"]) == 30
    assert cal["ingesta_objetivo_kcal"] == 2000.0

    assert dia(cal, date(2026, 11, 9))["estado"] == "fuera_del_plan"
    inicio = dia(cal, INICIO)
    assert inicio["dia_plan"] == 0 and inicio["peso_kg"] == 80.0
    assert dia(cal, date(2026, 11, 12))["estado"] == "registrado"
    assert dia(cal, date(2026, 11, 12))["cumplido"] is True
    assert dia(cal, date(2026, 11, 13))["cumplido"] is False
    assert dia(cal, date(2026, 11, 11))["estado"] == "estimado"
    assert dia(cal, date(2026, 11, 21))["estado"] == "futuro"
    # El gasto del 14 usa el último peso registrado (79 kg): 79 · 4 · 1 h = 316 kcal
    assert dia(cal, date(2026, 11, 14))["kcal_ejercicio"] == pytest.approx(316.0)


def test_calendario_mes_por_defecto_es_el_actual(cliente):
    assert cliente.get("/plans/active/calendario").json()["mes"] == "2026-11"


@pytest.mark.parametrize("mes", ["2026-13", "noviembre", "2026-1"])
def test_calendario_mes_invalido(cliente, mes):
    assert cliente.get("/plans/active/calendario", params={"mes": mes}).status_code == 422


def test_dia_del_plan_y_su_inversa():
    assert registro_service.dia_del_plan(PLAN, INICIO) == 0
    assert registro_service.dia_del_plan(PLAN, INICIO + timedelta(days=60)) == 60
    assert registro_service.dia_del_plan(PLAN, INICIO + timedelta(days=61)) is None
    assert registro_service.fecha_del_dia(PLAN, 5) == INICIO + timedelta(days=5)
