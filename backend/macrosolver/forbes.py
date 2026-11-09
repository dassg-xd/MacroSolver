"""Relación entre grasa y peso a lo largo de una pérdida (regla de Forbes).

Con p(F) = C / (C + F) y C = 10,4 · ρL / ρF, el modelo reparte la pérdida de
modo que dL/dF = 10,4 / F. Integrando desde (F0, L0):

    L(F) = L0 + 10,4 · ln(F / F0)        W(F) = F + L(F)

El reparto solo depende de la grasa, no de la ingesta ni del plazo: perder
ΔF kg de grasa siempre lleva al mismo peso. Por eso una meta en grasa se puede
traducir a una meta en peso y usar el mismo disparo con Secante.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .constantes import FORBES_KG, PCT_GRASA_FINAL_MIN
from .secante import secante_salvaguardada
from .tipos import ErrorMotor


def masa_libre_para_grasa(F0: float, L0: float, F: float) -> float:
    """Masa libre cuando la grasa llega a F (forma cerrada de Forbes)."""
    if F <= 0 or F0 <= 0:
        raise ErrorMotor("grasa_no_positiva", "La grasa debe ser positiva.")
    return L0 + FORBES_KG * math.log(F / F0)


def peso_para_grasa(F0: float, L0: float, F: float) -> float:
    """Peso total cuando la grasa llega a F."""
    return F + masa_libre_para_grasa(F0, L0, F)


def grasa_para_peso(F0: float, L0: float, W: float, tol: float = 1e-6) -> float:
    """Inversa de peso_para_grasa: grasa con la que se llega al peso W.

    g(F) = F + L0 + 10,4·ln(F/F0) − W es creciente en F, así que se resuelve
    con la misma Secante salvaguardada del disparo, en [F0/1000, F0].
    """
    W0 = F0 + L0
    if W > W0:
        raise ErrorMotor("meta_no_es_perdida", "El peso debe ser menor que el peso inicial.")
    if W == W0:
        return F0

    def g(F: float) -> float:
        return peso_para_grasa(F0, L0, F) - W

    a = F0 / 1000.0
    if g(a) > 0:
        raise ErrorMotor("peso_demasiado_bajo", "Ese peso no se alcanza con la grasa disponible.")
    return secante_salvaguardada(g, a, F0, tol=tol, max_iter=100).raiz


@dataclass(frozen=True)
class MetaGrasa:
    grasa_a_perder_kg: float
    grasa_final_kg: float
    masa_libre_final_kg: float
    peso_meta_kg: float
    pct_grasa_final: float
    pct_grasa_minimo: float

    @property
    def segura(self) -> bool:
        return self.pct_grasa_final >= self.pct_grasa_minimo


def meta_por_grasa(F0: float, L0: float, sexo: str, grasa_a_perder: float) -> MetaGrasa:
    """Peso al que se llega perdiendo `grasa_a_perder` kg de grasa."""
    if grasa_a_perder <= 0:
        raise ErrorMotor("meta_no_es_perdida", "La grasa a perder debe ser mayor que cero.")
    F = F0 - grasa_a_perder
    if F <= 0:
        raise ErrorMotor(
            "grasa_insuficiente",
            f"Tienes unos {F0:.1f} kg de grasa: no se pueden perder {grasa_a_perder:.1f} kg.",
        )
    L = masa_libre_para_grasa(F0, L0, F)
    W = F + L
    return MetaGrasa(
        grasa_a_perder_kg=grasa_a_perder,
        grasa_final_kg=F,
        masa_libre_final_kg=L,
        peso_meta_kg=W,
        pct_grasa_final=100.0 * F / W,
        pct_grasa_minimo=PCT_GRASA_FINAL_MIN[sexo],
    )
