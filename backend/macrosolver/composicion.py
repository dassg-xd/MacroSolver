"""Composición corporal inicial (5.3)."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .constantes import PCT_GRASA_MAX, PCT_GRASA_MIN
from .energia import imc
from .tipos import ErrorMotor, Perfil


@dataclass
class Composicion:
    pct_grasa: float
    F0: float
    L0: float
    metodo: str          # "marina" | "deurenberg"


def _log10_positivo(x: float, que: str) -> float:
    if x <= 0:
        raise ErrorMotor(
            "medidas_invalidas",
            f"Las medidas no son coherentes: {que} debe ser mayor que cero. Revisa cuello, cintura y cadera.",
        )
    return math.log10(x)


def grasa_marina(perfil: Perfil, cuello: float, cintura: float, cadera: float | None = None) -> float:
    """Fórmula de la Marina de EE. UU. (Hodgdon y Beckett, 1984). Medidas en cm."""
    H = perfil.altura_cm
    if perfil.sexo == "hombre":
        d = 1.0324 - 0.19077 * _log10_positivo(cintura - cuello, "cintura − cuello") + 0.15456 * math.log10(H)
    else:
        if cadera is None:
            raise ErrorMotor("falta_cadera", "Para mujeres la fórmula necesita la medida de cadera.")
        d = (1.29579 - 0.35004 * _log10_positivo(cintura + cadera - cuello, "cintura + cadera − cuello")
             + 0.22100 * math.log10(H))
    return 495.0 / d - 450.0


def grasa_deurenberg(perfil: Perfil, peso: float) -> float:
    """Respaldo por IMC (Deurenberg, 1991)."""
    s_ = 1.0 if perfil.sexo == "hombre" else 0.0
    return 1.20 * imc(peso, perfil.altura_cm) + 0.23 * perfil.edad - 10.8 * s_ - 5.4


def estimar_grasa(perfil: Perfil, peso: float, cuello: float | None = None, cintura: float | None = None,
                  cadera: float | None = None) -> Composicion:
    """%G, F0 y L0. Usa la Marina si hay medidas suficientes; si no, Deurenberg."""
    tiene_medidas = cuello is not None and cintura is not None and (perfil.sexo == "hombre" or cadera is not None)
    if tiene_medidas:
        pct, metodo = grasa_marina(perfil, cuello, cintura, cadera), "marina"
    else:
        pct, metodo = grasa_deurenberg(perfil, peso), "deurenberg"
    if not PCT_GRASA_MIN <= pct <= PCT_GRASA_MAX:
        raise ErrorMotor(
            "grasa_fuera_de_rango",
            f"El porcentaje de grasa estimado ({pct:.1f} %) está fuera del rango plausible "
            f"({PCT_GRASA_MIN:.0f} a {PCT_GRASA_MAX:.0f} %). Vuelve a tomar las medidas.",
        )
    F0 = pct / 100.0 * peso
    return Composicion(pct_grasa=pct, F0=F0, L0=peso - F0, metodo=metodo)


def composicion_desde_pct(peso: float, pct: float, metodo: str = "manual") -> Composicion:
    F0 = pct / 100.0 * peso
    return Composicion(pct_grasa=pct, F0=F0, L0=peso - F0, metodo=metodo)
