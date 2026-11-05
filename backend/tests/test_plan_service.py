"""Servicio de planeación: composición, viabilidad y vista previa."""
from datetime import date, timedelta

import pytest

from app.services.plan_service import ErrorPlan, vista_previa, crear_plan


USUARIO = {
    "id": 7,
    "correo": "ana@correo.com",
    "nombre": "Ana",
    "sexo": "Femenino",
    "fecha_nacimiento": "1995-04-12",
    "altura_cm": "165.0",
    "factor_actividad": "1.55",
    "nivel_entrenamiento": "principiante",
}


class RepositorioEnMemoria:
    def __init__(self) -> None:
        self.plan_guardado = None

    def buscar_activo(self, usuario_id: int):
        return self.plan_guardado

    def crear(self, usuario_id: int, plan: dict):
        self.plan_guardado = {"id": 1, "estado": "activo", "creado_en": "2026-11-05T10:00:00+00:00", **plan}
        return self.plan_guardado


def datos(**cambios):
    base = {
        "peso_inicial_kg": 80,
        "peso_objetivo_kg": 75,
        "fecha_inicio": date.today(),
        "fecha_meta": date.today() + timedelta(days=60),
        "cuello_cm": 34,
        "cintura_cm": 90,
        "cadera_cm": 100,
    }
    base.update(cambios)
    return base


def test_composicion_marina_con_medidas():
    previa = vista_previa(USUARIO, datos())
    assert previa["composicion"]["metodo"] == "marina"
    assert previa["composicion"]["pct_grasa"] > 0


def test_composicion_deurenberg_sin_medidas():
    previa = vista_previa(USUARIO, datos(cuello_cm=None, cintura_cm=None, cadera_cm=None))
    assert previa["composicion"]["metodo"] == "deurenberg"
    assert any("faltan medidas" in a for a in previa["advertencias"])


def test_preview_viable():
    previa = vista_previa(USUARIO, datos())
    assert previa["puede_confirmar"] is True
    assert previa["ingesta_kcal"] is not None
    assert previa["macros"]["proteina_g"] > 0
    assert previa["curva"] is not None
    assert len(previa["curva"]["peso_kg"]) == 61
    assert previa["perdida"]["peso_kg"] > 0
    assert previa["calculo"] is not None
    assert len(previa["calculo"]["secante"]["iteraciones"]) > 0
    assert previa["calculo"]["euler"]["error_maximo_kg"] is not None
    assert previa["sensibilidad"]["minimo_kcal"] is not None


def test_preview_plazo_corto():
    previa = vista_previa(
        USUARIO,
        datos(peso_inicial_kg=90, peso_objetivo_kg=80, fecha_meta=date.today() + timedelta(days=100)),
    )
    assert previa["puede_confirmar"] is False
    assert any(b["codigo"] == "plazo_no_viable" for b in previa["bloqueos"])
    assert previa["viabilidad"]["fecha_viable"] is not None
    assert previa["ingesta_kcal"] is None
    assert previa["viabilidad"]["ingesta_viable_kcal"] is not None


def test_preview_meta_no_es_perdida():
    previa = vista_previa(
        USUARIO,
        datos(peso_objetivo_kg=85, peso_inicial_kg=80),
    )
    assert previa["puede_confirmar"] is False
    assert any(b["codigo"] == "meta_no_es_perdida" for b in previa["bloqueos"])


def test_preview_imc_bajo():
    previa = vista_previa(
        USUARIO,
        datos(peso_inicial_kg=80, peso_objetivo_kg=45),
    )
    assert previa["puede_confirmar"] is False
    assert any(b["codigo"] == "imc_bajo" for b in previa["bloqueos"])


def test_preview_fuera_de_horizonte():
    previa = vista_previa(
        USUARIO,
        datos(peso_inicial_kg=100, peso_objetivo_kg=80, fecha_meta=date.today() + timedelta(days=200)),
    )
    assert previa["puede_confirmar"] is False
    assert any(b["codigo"] == "fuera_de_horizonte" for b in previa["bloqueos"])


def test_preview_meta_inalcanzable():
    previa = vista_previa(
        USUARIO,
        datos(peso_inicial_kg=120, peso_objetivo_kg=60, fecha_meta=date.today() + timedelta(days=730)),
    )
    assert previa["puede_confirmar"] is False
    assert any(b["codigo"] == "meta_inalcanzable" for b in previa["bloqueos"])


def test_preview_medidas_invalidas_lanza_error():
    with pytest.raises(Exception):
        vista_previa(USUARIO, datos(cuello_cm=100, cintura_cm=30))


def test_crear_plan_rechaza_bloqueos():
    repo = RepositorioEnMemoria()
    with pytest.raises(ErrorPlan) as error:
        crear_plan(USUARIO, datos(peso_objetivo_kg=85, peso_inicial_kg=80), repo)
    assert error.value.status_code == 422


def test_crear_plan_guarda_y_devuelve_plan():
    repo = RepositorioEnMemoria()
    plan = crear_plan(USUARIO, datos(), repo)
    assert plan["id"] == 1
    assert plan["ingesta_kcal"] is not None
    assert plan["composicion"]["metodo"] == "marina"
    assert repo.plan_guardado is not None
    assert repo.plan_guardado["masa_libre_inicial_kg"] is not None
    assert repo.plan_guardado["metodo_grasa"] == "marina"
    assert repo.plan_guardado["estado"] == "activo"
    assert plan["dias_restantes"] >= 0
