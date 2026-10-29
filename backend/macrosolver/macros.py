"""Macronutrientes (5.8): aritmética."""
from __future__ import annotations

from dataclasses import dataclass

from .constantes import (FRACCION_GRASA, FRACCION_GRASA_RESPALDO, KCAL_G_CHO, KCAL_G_GRASA,
                         KCAL_G_PROTEINA, PROTEINA_G_POR_KG_LIBRE)
from .tipos import ErrorMotor


@dataclass
class Macros:
    proteina_g: float
    grasa_g: float
    carbohidratos_g: float
    fraccion_grasa: float
    advertencia: str | None = None


def macros(ingesta: float, L0: float) -> Macros:
    P = PROTEINA_G_POR_KG_LIBRE * L0
    for frac in (FRACCION_GRASA, FRACCION_GRASA_RESPALDO):
        G = frac * ingesta / KCAL_G_GRASA
        CHO = (ingesta - KCAL_G_PROTEINA * P - frac * ingesta) / KCAL_G_CHO
        if CHO >= 0:
            aviso = None if frac == FRACCION_GRASA else "La grasa se bajó al 20 % para que alcancen los carbohidratos."
            return Macros(P, G, CHO, frac, aviso)
    raise ErrorMotor("macros_imposibles",
                     "Con esta ingesta la proteína necesaria no deja espacio para carbohidratos. Revisa la meta o el plazo.")
