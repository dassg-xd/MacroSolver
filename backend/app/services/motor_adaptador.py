"""Puente entre los datos de la app (base de datos y API) y el motor numérico.

La app guarda el sexo como 'Masculino' / 'Femenino' (usuario.sexo, plan.sexo);
el motor espera 'hombre' / 'mujer'. Solo esta capa traduce, así el motor no cambia
y las pruebas de la beta (V5) siguen pasando.
"""
from datetime import date
from decimal import Decimal
from typing import Any, Literal, Mapping

from macrosolver import ErrorMotor, Perfil

from app.schemas.auth import calcular_edad

SexoApp = Literal["Masculino", "Femenino"]
SexoMotor = Literal["hombre", "mujer"]

_A_MOTOR: dict[str, SexoMotor] = {"Masculino": "hombre", "Femenino": "mujer"}
_A_APP: dict[str, SexoApp] = {motor: app for app, motor in _A_MOTOR.items()}


def sexo_a_motor(sexo: str) -> SexoMotor:
    try:
        return _A_MOTOR[sexo]
    except KeyError as error:
        raise ErrorMotor("sexo_invalido", "El sexo debe ser «Masculino» o «Femenino».") from error


def sexo_a_app(sexo: str) -> SexoApp:
    try:
        return _A_APP[sexo]
    except KeyError as error:
        raise ErrorMotor("sexo_invalido", "El sexo debe ser «hombre» o «mujer».") from error


def _fecha(valor: date | str) -> date:
    return valor if isinstance(valor, date) else date.fromisoformat(str(valor))


def perfil_desde_usuario(usuario: Mapping[str, Any], hoy: date | None = None) -> Perfil:
    """Perfil del motor a partir de una fila de 'usuario' (edad calculada a la fecha 'hoy')."""
    return Perfil(
        sexo=sexo_a_motor(usuario["sexo"]),
        edad=calcular_edad(_fecha(usuario["fecha_nacimiento"]), hoy),
        altura_cm=float(Decimal(str(usuario["altura_cm"]))),
        f_act=float(Decimal(str(usuario["factor_actividad"]))),
    )


def perfil_desde_plan(plan: Mapping[str, Any]) -> Perfil:
    """Perfil del motor a partir de la copia guardada en una fila de 'plan'."""
    return Perfil(
        sexo=sexo_a_motor(plan["sexo"]),
        edad=int(plan["edad_anios"]),
        altura_cm=float(Decimal(str(plan["altura_cm"]))),
        f_act=float(Decimal(str(plan["factor_actividad"]))),
    )
