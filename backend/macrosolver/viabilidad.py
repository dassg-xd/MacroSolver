"""Viabilidad de la meta (5.6, versión corregida)."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .constantes import DEFICIT_MAXIMO, INGESTA_MINIMA
from .energia import equilibrio, tdee, tmb
from .modelo import derivadas
from .tipos import ErrorMotor, Perfil

DIAS_MAXIMOS_BUSQUEDA = 3650


def ingesta_minima(peso: float, perfil: Perfil) -> float:
    """I_min(W) = max(TMB(W), 1500 hombres | 1200 mujeres)."""
    return max(tmb(peso, perfil), INGESTA_MINIMA[perfil.sexo])


def ingesta_rapida(W0: float, perfil: Perfil) -> float:
    """Ingesta constante más rápida permitida: max(TDEE(W0) − 700, I_min(W0))."""
    return max(tdee(W0, perfil) - DEFICIT_MAXIMO, ingesta_minima(W0, perfil))


def cumple_bloqueos(ingesta: float, W0: float, perfil: Perfil) -> bool:
    """Basta revisar el día 0: TMB y TDEE son máximos ahí porque el peso baja."""
    return ingesta >= ingesta_minima(W0, perfil) - 1e-9 and tdee(W0, perfil) - ingesta <= DEFICIT_MAXIMO + 1e-9


@dataclass
class Viabilidad:
    viable: bool
    alcanzable: bool         # False si ni con I_ráp se llega nunca
    i_rapida: float
    n_min: float | None      # días (con fracción) para llegar con I_ráp
    n_min_dias: int | None   # ⌈n_min⌉
    mensaje: str


def evaluar_viabilidad(F0: float, L0: float, perfil: Perfil, W_meta: float, N: int) -> Viabilidad:
    W0 = F0 + L0
    if W_meta >= W0:
        raise ErrorMotor("meta_no_es_perdida", "El modelo solo planea pérdida de peso: la meta debe ser menor que el peso inicial.")
    I_rap = ingesta_rapida(W0, perfil)

    if equilibrio(I_rap, perfil) >= W_meta:
        return Viabilidad(False, False, I_rap, None, None,
                          "La meta no se puede alcanzar con una ingesta segura: incluso con el déficit máximo "
                          "permitido el peso se estabiliza por encima de la meta.")

    # Euler con I_ráp hasta cruzar la meta; interpolación lineal para la fracción de día.
    F, L = F0, L0
    W_prev = W0
    for i in range(DIAS_MAXIMOS_BUSQUEDA):
        dF, dL, _ = derivadas(F, L, I_rap, perfil)
        F += dF
        L += dL
        W = F + L
        if W <= W_meta:
            frac = (W_prev - W_meta) / (W_prev - W)
            n_min = i + frac
            n_dias = math.ceil(n_min - 1e-12)
            viable = N >= n_dias
            msg = ("La meta es viable." if viable else
                   f"El plazo es demasiado corto: lo más pronto que se puede llegar con seguridad es en {n_dias} días.")
            return Viabilidad(viable, True, I_rap, n_min, n_dias, msg)
        W_prev = W
    return Viabilidad(False, False, I_rap, None, None, "La meta no se alcanza en un plazo razonable.")
