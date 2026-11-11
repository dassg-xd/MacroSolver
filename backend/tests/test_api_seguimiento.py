"""Seguimiento, re-planeación, estadísticas, historial y guía, sin red."""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from apoyo import Planes, Registros, cliente_con, dias_atras, plan_de_prueba
from app.main import app

N = 90


@pytest.fixture
def escenario():
    """Plan de 80 a 76 kg en 90 días, iniciado hace `dias` días."""
    def crear(dias: int = 30):
        planes = Planes(plan_de_prueba(dias_atras(dias), N))
        registros = Registros()
        return planes, registros, cliente_con(planes, registros)
    yield crear
    app.dependency_overrides.clear()


def desviar(planes, registros, dias: int, peso: float = 80.0, kcal: float = 2600.0):
    """El usuario come de más y su peso no baja: registra `dias` días."""
    plan = planes.activo
    inicio = date.fromisoformat(plan["fecha_inicio"])
    for i in range(dias + 1):
        registros.guardar_calorias(plan["id"], inicio + timedelta(days=i), kcal)
    for i in range(5, dias + 1, 5):
        registros.guardar_peso(plan["id"], inicio + timedelta(days=i), peso)


# ----------------------------------------------------------------- seguimiento
def test_seguimiento_sin_registros(escenario):
    _, _, c = escenario()
    s = c.get("/plans/active/seguimiento").json()
    assert s["dia_actual"] == 30 and s["plazo_dias"] == N
    assert len(s["dias"]) == len(s["curva_ideal"]) == len(s["curva_adherencia"]) == N + 1
    assert s["curva_ideal"][0] == 80.0
    assert s["curva_ideal"][-1] == pytest.approx(76.0, abs=0.02)
    assert s["curva_adherencia"] == s["curva_ideal"]      # sin registros todo es «estimado»
    assert all(s["estimado"])
    assert s["pesos"] == [{"dia": 0, "fecha": dias_atras(30).isoformat(), "peso_kg": 80.0}]
    assert s["tendencia"] is None
    assert s["desviacion"]["sugerir"] is False
    assert s["hoy"]["dias_restantes"] == 60 and s["hoy"]["kcal"] is None


def test_seguimiento_con_desviacion(escenario):
    planes, registros, c = escenario()
    desviar(planes, registros, 30)
    s = c.get("/plans/active/seguimiento").json()
    assert s["curva_adherencia"][30] > s["curva_ideal"][30] + 1
    assert not any(s["estimado"][:31]) and all(s["estimado"][31:])
    assert s["tendencia"]["n"] == 7 and len(s["tendencia"]["curva"]) == N + 1
    assert s["desviacion"]["sugerir"] is True
    assert s["desviacion"]["delta_kg"] > 1.0
    assert "por encima" in s["desviacion"]["motivo"]
    assert s["llegada"]["retraso_dias"] is None or s["llegada"]["retraso_dias"] > 0
    assert s["hoy"]["kcal"] == 2600.0 and s["hoy"]["ultimo_peso_kg"] == 80.0


def test_seguimiento_con_ejercicio(escenario):
    planes, registros, c = escenario()
    desviar(planes, registros, 10, kcal=1900.0)
    registros.reemplazar_actividades(42, dias_atras(25), [{"actividad_id": 5, "minutos": 60}])
    s = c.get("/plans/active/seguimiento").json()
    assert s["curva_ejercicio"] is not None and len(s["curva_ejercicio"]) == N + 1
