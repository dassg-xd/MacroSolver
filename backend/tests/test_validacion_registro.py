"""Validaciones del registro: edad mínima 18 años y contraseña de 8 caracteres o más."""
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegistroRequest, calcular_edad


def datos(**cambios):
    base = {
        "correo": "ana@correo.com",
        "contrasena": "clave-segura",
        "nombre": "Ana",
        "sexo": "Femenino",
        "fecha_nacimiento": "1995-04-12",
        "altura_cm": 165,
        "factor_actividad": "1.55",
    }
    base.update(cambios)
    return base


def mensajes(error: ValidationError) -> str:
    return " ".join(e["msg"] for e in error.errors())


def hace_anios(n: int, dias: int = 0) -> str:
    hoy = date.today()
    try:
        d = hoy.replace(year=hoy.year - n)
    except ValueError:            # 29 de febrero
        d = hoy.replace(year=hoy.year - n, day=28)
    return date.fromordinal(d.toordinal() + dias).isoformat()


def test_registro_valido():
    assert RegistroRequest(**datos()).nombre == "Ana"


def test_cumple_18_hoy_es_valido():
    RegistroRequest(**datos(fecha_nacimiento=hace_anios(18)))


def test_le_falta_un_dia_para_18():
    with pytest.raises(ValidationError) as e:
        RegistroRequest(**datos(fecha_nacimiento=hace_anios(18, dias=1)))
    assert "al menos 18 años" in mensajes(e.value)


def test_mas_de_100_anios():
    with pytest.raises(ValidationError) as e:
        RegistroRequest(**datos(fecha_nacimiento=hace_anios(101)))
    assert "fecha de nacimiento" in mensajes(e.value)


@pytest.mark.parametrize("clave", ["", "1234567", "corta"])
def test_contrasena_corta(clave):
    with pytest.raises(ValidationError) as e:
        RegistroRequest(**datos(contrasena=clave))
    assert "al menos 8 caracteres" in mensajes(e.value)


def test_contrasena_solo_espacios():
    with pytest.raises(ValidationError) as e:
        RegistroRequest(**datos(contrasena=" " * 10))
    assert "solo espacios" in mensajes(e.value)


def test_contrasena_de_8_es_valida():
    RegistroRequest(**datos(contrasena="12345678"))


def test_calcular_edad():
    assert calcular_edad(date(2000, 6, 15), date(2026, 6, 14)) == 25
    assert calcular_edad(date(2000, 6, 15), date(2026, 6, 15)) == 26
