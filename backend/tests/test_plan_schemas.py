"""Esquemas de planeación: fechas, plazo y pesos."""
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.plan import DatosPlanRequest


def datos(**cambios):
    base = {
        "peso_inicial_kg": 80,
        "peso_objetivo_kg": 75,
        "fecha_meta": date.today() + timedelta(days=60),
    }
    base.update(cambios)
    return base


def test_fecha_inicio_por_defecto_es_hoy():
    plan = DatosPlanRequest(**datos())
    assert plan.fecha_inicio == date.today()
    assert plan.plazo_dias == 60


def test_fecha_inicio_editable():
    inicio = date.today() - timedelta(days=5)
    plan = DatosPlanRequest(**datos(fecha_inicio=inicio))
    assert plan.fecha_inicio == inicio
    assert plan.plazo_dias == 65


def test_fecha_inicio_futura_rechazada():
    with pytest.raises(ValidationError) as error:
        DatosPlanRequest(**datos(fecha_inicio=date.today() + timedelta(days=1)))
    assert "futura" in str(error.value)


def test_fecha_meta_posterior():
    with pytest.raises(ValidationError) as error:
        DatosPlanRequest(**datos(fecha_meta=date.today()))
    assert "posterior" in str(error.value)


def test_plazo_minimo():
    with pytest.raises(ValidationError) as error:
        DatosPlanRequest(**datos(fecha_meta=date.today() + timedelta(days=1)))
    assert "al menos" in str(error.value)


def test_plazo_maximo():
    with pytest.raises(ValidationError) as error:
        DatosPlanRequest(**datos(fecha_meta=date.today() + timedelta(days=731)))
    assert "superar" in str(error.value)


def test_peso_fuera_de_rango():
    with pytest.raises(ValidationError):
        DatosPlanRequest(**datos(peso_inicial_kg=5))
    with pytest.raises(ValidationError):
        DatosPlanRequest(**datos(peso_objetivo_kg=400))


def test_campo_desconocido():
    with pytest.raises(ValidationError):
        DatosPlanRequest(**datos(desconocido=1))
