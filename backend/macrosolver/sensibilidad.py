"""Sensibilidad por diferencias finitas (5.11)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .composicion import composicion_desde_pct
from .secante import calcular_ingesta_meta
from .tipos import ErrorMotor, Perfil
from .viabilidad import evaluar_viabilidad


def derivada_central(g: Callable[[float], float], theta: float, delta: float) -> float:
    """(g(θ+Δ) − g(θ−Δ)) / 2Δ, error O(Δ²)."""
    return (g(theta + delta) - g(theta - delta)) / (2.0 * delta)


def derivada_progresiva(g: Callable[[float], float], theta: float, delta: float) -> float:
    """(g(θ+Δ) − g(θ)) / Δ, error O(Δ). Solo para comparar en V6."""
    return (g(theta + delta) - g(theta)) / delta


@dataclass
class RangoIngesta:
    minimo: float
    maximo: float
    variantes: dict[str, float]
    omitidas: list[str]      # variantes con las que la meta no es viable en el plazo


def _ingesta_para(perfil: Perfil, W0: float, pct: float, N: int, W_meta: float) -> float | None:
    comp = composicion_desde_pct(W0, pct)
    v = evaluar_viabilidad(comp.F0, comp.L0, perfil, W_meta, N)
    if not v.viable:
        return None
    try:
        return calcular_ingesta_meta(comp.F0, comp.L0, perfil, N, W_meta, v.i_rapida).raiz
    except ErrorMotor:
        return None


def rango_ingesta(perfil: Perfil, W0: float, pct_grasa: float, N: int, W_meta: float, I_star: float,
                  var_f_act: float = 0.10, var_pct: float = 3.0) -> RangoIngesta:
    """Recalcula I* con f_act·(1 ± 10 %) y %G ± 3 puntos, uno a la vez. Las variantes inviables se omiten."""
    variantes = {"base": I_star}
    omitidas: list[str] = []
    for nombre, p, pct in (
        ("f_act −10 %", perfil.con_f_act(perfil.f_act * (1 - var_f_act)), pct_grasa),
        ("f_act +10 %", perfil.con_f_act(perfil.f_act * (1 + var_f_act)), pct_grasa),
        ("%G −3", perfil, pct_grasa - var_pct),
        ("%G +3", perfil, pct_grasa + var_pct),
    ):
        I = _ingesta_para(p, W0, pct, N, W_meta)
        if I is not None:
            variantes[nombre] = I
        else:
            omitidas.append(nombre)
    vals = list(variantes.values())
    return RangoIngesta(min(vals), max(vals), variantes, omitidas)
