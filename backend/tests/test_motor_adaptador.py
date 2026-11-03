"""La app usa Masculino/Femenino; el motor, hombre/mujer. El adaptador traduce en los dos sentidos."""
from datetime import date

import pytest

from app.services.motor_adaptador import (perfil_desde_plan, perfil_desde_usuario, sexo_a_app,
                                          sexo_a_motor)
from macrosolver import ErrorMotor, Perfil, tdee

USUARIO = {
    "sexo": "Masculino",
    "fecha_nacimiento": "2003-05-20",
    "altura_cm": "176.0",
    "factor_actividad": "1.375",
}


@pytest.mark.parametrize("app,motor", [("Masculino", "hombre"), ("Femenino", "mujer")])
def test_ida_y_vuelta(app, motor):
    assert sexo_a_motor(app) == motor
    assert sexo_a_app(motor) == app


@pytest.mark.parametrize("valor", ["hombre", "masculino", "M", ""])
def test_sexo_desconocido_en_la_app(valor):
    with pytest.raises(ErrorMotor) as e:
        sexo_a_motor(valor)
    assert e.value.codigo == "sexo_invalido"


def test_perfil_desde_usuario_calcula_la_edad():
    p = perfil_desde_usuario(USUARIO, hoy=date(2026, 11, 2))
    assert p == Perfil("hombre", 23, 176.0, 1.375)


def test_perfil_desde_usuario_da_el_mismo_tdee_que_el_motor():
    p = perfil_desde_usuario(USUARIO, hoy=date(2026, 11, 2))
    assert tdee(82.0, p) == pytest.approx(tdee(82.0, Perfil("hombre", 23, 176, 1.375)))


def test_perfil_desde_plan():
    plan = {"sexo": "Femenino", "edad_anios": 30, "altura_cm": 162, "factor_actividad": "1.55"}
    assert perfil_desde_plan(plan) == Perfil("mujer", 30, 162.0, 1.55)
