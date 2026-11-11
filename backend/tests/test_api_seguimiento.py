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


# ----------------------------------------------------------------- re-planeación
def test_replanear_sin_pesos_422(escenario):
    _, _, c = escenario()
    r = c.post("/plans/active/replanear/preview")
    assert r.status_code == 422
    assert "peso" in r.json()["detail"]


def test_vista_previa_de_replaneacion(escenario):
    planes, registros, c = escenario()
    desviar(planes, registros, 30)
    r = c.post("/plans/active/replanear/preview")
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["puede_confirmar"] is True, p["bloqueos"]
    assert p["plazo_dias"] == 60                       # días restantes desde el último peso
    assert p["fecha_inicio"] == dias_atras(0).isoformat()
    assert p["fecha_meta"] == (dias_atras(30) + timedelta(days=N)).isoformat()
    rep = p["replaneacion"]
    assert rep["sugerida"] is True and rep["peso_real_kg"] == 80.0 and rep["dia_ultimo_peso"] == 30
    assert p["ingesta_kcal"] < rep["actual"]["ingesta_kcal"]   # menos tiempo, mismo peso
    assert len(planes.todos) == 1                      # no guarda nada


def test_replanear_crea_plan_encadenado_y_copia_registros(escenario):
    planes, registros, c = escenario()
    desviar(planes, registros, 30)
    r = c.post("/plans/active/replanear")
    assert r.status_code == 201, r.text
    nuevo = planes.activo
    assert nuevo["id"] != 42 and nuevo["plan_previo_id"] == 42
    assert nuevo["peso_inicial_kg"] == 80.0 and nuevo["plazo_dias"] == 60
    assert nuevo["sexo"] == "Femenino" and nuevo["edad_anios"] == 31
    assert abs(nuevo["grasa_inicial_kg"] + nuevo["masa_libre_inicial_kg"] - 80.0) <= 0.05
    assert next(p for p in planes.todos if p["id"] == 42)["estado"] == "inactivo"
    # Las calorías del nuevo día 0 (hoy) pasan al plan nuevo.
    assert registros.calorias[nuevo["id"]] == {dias_atras(0): 2600.0}


def test_replaneacion_inviable_ofrece_fecha_viable(escenario):
    planes, registros, c = escenario(dias=75)
    desviar(planes, registros, 75)
    p = c.post("/plans/active/replanear/preview").json()
    assert p["puede_confirmar"] is False
    assert p["bloqueos"][0]["codigo"] == "plazo_no_viable"
    viable = p["viabilidad"]["fecha_viable"]
    assert viable is not None
    assert c.post("/plans/active/replanear").status_code == 422

    p2 = c.post("/plans/active/replanear/preview", json={"fecha_meta": viable}).json()
    assert p2["puede_confirmar"] is True, p2["bloqueos"]
    assert c.post("/plans/active/replanear", json={"fecha_meta": viable}).status_code == 201
    assert planes.activo["plan_previo_id"] == 42


def test_replanear_con_meta_alcanzada(escenario):
    planes, registros, c = escenario()
    registros.guardar_peso(42, dias_atras(5), 75.5)
    r = c.post("/plans/active/replanear/preview")
    assert r.status_code == 422 and "meta" in r.json()["detail"]


# ----------------------------------------------------------------- estadísticas
def test_estadisticas(escenario):
    planes, registros, c = escenario()
    desviar(planes, registros, 30, kcal=planes.todos[0]["ingesta_kcal"])
    registros.reemplazar_actividades(42, dias_atras(3), [{"actividad_id": 5, "minutos": 60}])
    e = c.get("/plans/active/estadisticas").json()
    res = e["resumen"]
    assert res["dias_transcurridos"] == 31 and res["dias_registrados"] == 31
    assert res["adherencia_pct"] == 100.0
    assert res["cambio_kg"] == 0.0 and res["sesiones"] == 1 and res["minutos"] == 60
    assert 5 <= len(e["semanas"]) <= 6
    assert e["semanas"][-1]["parcial"] is True
    assert sum(s["dias_registrados"] for s in e["semanas"]) == 31
    assert sum(s["sesiones"] for s in e["semanas"]) == 1


# ----------------------------------------------------------------- historial
def test_historial(escenario):
    planes, registros, c = escenario()
    desviar(planes, registros, 30)
    c.post("/plans/active/replanear")
    h = c.get("/plans").json()
    assert [p["estado"] for p in h] == ["activo", "inactivo"]
    assert h[0]["plan_previo_id"] == h[1]["id"] == 42
    assert h[1]["ultimo_peso_kg"] == 80.0 and h[1]["cambio_kg"] == 0.0
    assert h[0]["ultimo_peso_kg"] is None
