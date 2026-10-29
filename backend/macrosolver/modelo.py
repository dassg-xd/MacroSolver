"""Modelo de dos compartimentos (5.4), Euler (5.5) y soluciones de referencia.

Convención: la ingesta del día i lleva de W_i a W_(i+1).
"""
from __future__ import annotations

import math
from typing import Callable, Mapping, Sequence, Union

from .constantes import C_F, FACTOR_BASE_EJERCICIO, RHO_F, RHO_L, RHO_SIMPLE
from .energia import coeficientes_tdee, equilibrio, tdee, tmb
from .tipos import Perfil, Trayectoria

Ingesta = Union[float, Sequence[float], Callable[[int], float]]


def fraccion_libre(F: float) -> float:
    """p(F) = c_F / (c_F + F): fracción del balance que va a la masa libre."""
    return C_F / (C_F + F)


def _ingesta_del_dia(ingesta: Ingesta, dia: int) -> float:
    if callable(ingesta):
        return float(ingesta(dia))
    if isinstance(ingesta, (int, float)):
        return float(ingesta)
    return float(ingesta[dia])


def derivadas(F: float, L: float, I: float, perfil: Perfil, gasto_extra: float | None = None) -> tuple[float, float, float]:
    """(dF/dt, dL/dt, B). Si gasto_extra no es None se usa el modelo con ejercicio (5.12)."""
    W = F + L
    if gasto_extra is None:
        B = I - tdee(W, perfil)
    else:
        B = I - FACTOR_BASE_EJERCICIO * tmb(W, perfil) - W * gasto_extra
    p = fraccion_libre(F)
    return (1.0 - p) * B / RHO_F, p * B / RHO_L, B


def simular_composicion(F0: float, L0: float, perfil: Perfil, ingesta: Ingesta, dias: int, h: float = 1.0,
                        ejercicio: Mapping[int, float] | None = None,
                        dias_registrados: set[int] | None = None) -> Trayectoria:
    """Euler explícito sobre (F, L) durante `dias` días con paso h (en días).

    ejercicio: {día: E_i} con E_i = Σ (MET_j − 1)·horas_j. Si se pasa, los días de
    `dias_registrados` usan factor base 1,2 más el gasto de actividad (5.12);
    los demás días usan f_act.
    """
    pasos = int(round(dias / h))
    F, L = float(F0), float(L0)
    t_, Ws, Fs, Ls, Bs = [0.0], [F + L], [F], [L], []
    for n in range(pasos):
        t = n * h
        dia = int(math.floor(t + 1e-12))
        I = _ingesta_del_dia(ingesta, dia)
        extra = None
        if ejercicio is not None and dias_registrados is not None and dia in dias_registrados:
            extra = ejercicio.get(dia, 0.0)
        dF, dL, B = derivadas(F, L, I, perfil, extra)
        F += h * dF
        L += h * dL
        t_.append((n + 1) * h)
        Ws.append(F + L)
        Fs.append(F)
        Ls.append(L)
        Bs.append(B)
    return Trayectoria(t=t_, W=Ws, F=Fs, L=Ls, B=Bs)


def referencia_rk4(F0: float, L0: float, perfil: Perfil, ingesta: float, dias: int, h: float = 0.05) -> Trayectoria:
    """RK4 del modelo no lineal con ingesta constante. Solo para medir el error de Euler (V1)."""
    pasos = int(round(dias / h))
    F, L = float(F0), float(L0)
    t_, Ws, Fs, Ls = [0.0], [F + L], [F], [L]

    def f(F_, L_):
        dF, dL, _ = derivadas(F_, L_, ingesta, perfil)
        return dF, dL

    for n in range(pasos):
        k1 = f(F, L)
        k2 = f(F + h / 2 * k1[0], L + h / 2 * k1[1])
        k3 = f(F + h / 2 * k2[0], L + h / 2 * k2[1])
        k4 = f(F + h * k3[0], L + h * k3[1])
        F += h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        L += h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        t_.append((n + 1) * h)
        Ws.append(F + L)
        Fs.append(F)
        Ls.append(L)
    return Trayectoria(t=t_, W=Ws, F=Fs, L=Ls, B=[])


# ---------------------------------------------------------------- modelo lineal (beta)

def euler_simple(W0: float, perfil: Perfil, ingesta: Ingesta, dias: int, h: float = 1.0,
                 rho: float = RHO_SIMPLE) -> list[float]:
    """Modelo de un compartimento de la beta: dW/dt = (I − TDEE(W)) / ρ."""
    pasos = int(round(dias / h))
    W = float(W0)
    out = [W]
    for n in range(pasos):
        dia = int(math.floor(n * h + 1e-12))
        I = _ingesta_del_dia(ingesta, dia)
        W += h * (I - tdee(W, perfil)) / rho
        out.append(W)
    return out


def solucion_exacta_lineal(W0: float, perfil: Perfil, ingesta: float, t: float, rho: float = RHO_SIMPLE) -> float:
    """W(t) = W* + (W0 − W*)·e^(−(a/ρ)·t), para ingesta constante."""
    a, _ = coeficientes_tdee(perfil)
    Wst = equilibrio(ingesta, perfil)
    return Wst + (W0 - Wst) * math.exp(-(a / rho) * t)


def recurrencia_exacta_lineal(W0: float, perfil: Perfil, ingesta: float, i: int, h: float = 1.0,
                              rho: float = RHO_SIMPLE) -> float:
    """Forma cerrada de Euler en el caso lineal: W_i = W* + (W0 − W*)·(1 − z)^i, z = h·a/ρ."""
    a, _ = coeficientes_tdee(perfil)
    z = h * a / rho
    Wst = equilibrio(ingesta, perfil)
    return Wst + (W0 - Wst) * (1.0 - z) ** i
