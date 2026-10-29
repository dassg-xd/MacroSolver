"""Seguimiento, tendencia y re-planeación (5.9)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

from .composicion import grasa_deurenberg
from .constantes import (DIA_MINIMO_REPLANEACION, HORIZONTE_LLEGADA, MAX_DIAS_SIN_REGISTRO,
                         PESOS_MINIMOS_REPLANEACION, TOLERANCIA_REPLANEACION)
from .modelo import simular_composicion
from .tipos import ErrorMotor, Perfil, Trayectoria


# ---------------------------------------------------------------- curva por adherencia

def simular_adherencia(F0: float, L0: float, perfil: Perfil, ingesta_plan: float, dias: int,
                       calorias: Mapping[int, float],
                       ejercicio: Mapping[int, float] | None = None) -> Trayectoria:
    """Euler con la ingesta real de los días registrados y I* en los demás («estimado»).

    calorias: {día i: kcal}. La ingesta del día i lleva de W_i a W_(i+1).
    ejercicio: {día i: E_i}; si se pasa, da la curva «con ejercicio» (5.12).
    """
    def ingesta(i: int) -> float:
        return calorias.get(i, ingesta_plan)

    tr = simular_composicion(F0, L0, perfil, ingesta, dias, ejercicio=ejercicio,
                             dias_registrados=set(calorias) if ejercicio is not None else None)
    tr.estimado = [i not in calorias for i in range(dias + 1)]
    return tr


@dataclass
class Llegada:
    dia: int | None          # None si no cruza dentro del horizonte
    retraso: int | None
    mensaje: str


def llegada_estimada(F0: float, L0: float, perfil: Perfil, ingesta_plan: float, N: int,
                     calorias: Mapping[int, float], W_meta: float,
                     horizonte: int = HORIZONTE_LLEGADA) -> Llegada:
    """Curva por adherencia extendida con I* hasta el horizonte; primer día con W ≤ meta."""
    h = max(horizonte, N)
    tr = simular_adherencia(F0, L0, perfil, ingesta_plan, h, calorias)
    for i, W in enumerate(tr.W):
        if W <= W_meta:
            return Llegada(i, i - N, "A tiempo." if i <= N else f"{i - N} días de retraso.")
    return Llegada(None, None, "Con este ritmo la meta no se alcanza en el horizonte de simulación.")


# ---------------------------------------------------------------- tendencia

@dataclass
class Tendencia:
    C: float
    A: float
    r2: float
    n: int

    def evaluar(self, x: float) -> float:
        return self.C * math.exp(self.A * x)

    @property
    def tasa_semanal(self) -> float:
        """Cambio relativo por semana: e^(7A) − 1."""
        return math.exp(7 * self.A) - 1.0


def regresion_exponencial(xs: list[float], ys: list[float]) -> Tendencia:
    """ŷ = C·e^(A·x) por mínimos cuadrados sobre ln y. R² se reporta en kg."""
    n = len(xs)
    if n != len(ys):
        raise ValueError("xs y ys deben tener la misma longitud")
    if any(y <= 0 for y in ys):
        raise ErrorMotor("peso_no_positivo", "Todos los pesos deben ser positivos.")
    if len(set(xs)) < 2:
        raise ErrorMotor("pocos_pesos", "La tendencia necesita al menos dos pesos en días distintos.")
    zs = [math.log(y) for y in ys]
    Sx, Sz = sum(xs), sum(zs)
    Sxz = sum(x * z for x, z in zip(xs, zs))
    Sxx = sum(x * x for x in xs)
    A = (n * Sxz - Sx * Sz) / (n * Sxx - Sx * Sx)
    lnC = Sz / n - A * Sx / n
    C = math.exp(lnC)
    y_bar = sum(ys) / n
    ss_res = sum((y - C * math.exp(A * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - y_bar) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return Tendencia(C, A, r2, n)


def calcular_tendencia(pesos: Mapping[int, float]) -> Tendencia:
    dias = sorted(pesos)
    return regresion_exponencial([float(d) for d in dias], [pesos[d] for d in dias])


# ---------------------------------------------------------------- re-planeación

@dataclass
class Desviacion:
    delta: float | None          # ŷ(x_u) − W_ideal(x_u): dispara la sugerencia
    delta_meta: float | None     # ŷ(N) − W_meta: informativa
    delta_modelo: float | None   # ŷ(x_u) − W_adherencia(x_u): informativa
    sugerir: bool
    motivo: str


def evaluar_replaneacion(pesos: Mapping[int, float], curva_ideal: list[float], curva_adherencia: list[float],
                         W_meta: float, N: int, dia_actual: int, dias_con_registro: set[int],
                         tol: float = TOLERANCIA_REPLANEACION) -> Desviacion:
    """Regla: |δ| > tol, al menos 3 pesos, x_u ≥ 10 y no más de 7 días seguidos sin registro."""
    if len(set(pesos)) < 2:
        return Desviacion(None, None, None, False, "Faltan pesos para calcular la tendencia.")
    tend = calcular_tendencia(pesos)
    x_u = max(pesos)
    idx = min(x_u, len(curva_ideal) - 1)
    y_u = tend.evaluar(x_u)
    delta = y_u - curva_ideal[idx]
    delta_meta = tend.evaluar(N) - W_meta
    delta_modelo = y_u - curva_adherencia[min(x_u, len(curva_adherencia) - 1)]

    ultimo = max(dias_con_registro) if dias_con_registro else 0
    sin_registro = dia_actual - ultimo
    if len(pesos) < PESOS_MINIMOS_REPLANEACION:
        return Desviacion(delta, delta_meta, delta_modelo, False, "Se necesitan al menos 3 pesos.")
    if x_u < DIA_MINIMO_REPLANEACION:
        return Desviacion(delta, delta_meta, delta_modelo, False, "No se evalúa antes del día 10.")
    if sin_registro > MAX_DIAS_SIN_REGISTRO:
        return Desviacion(delta, delta_meta, delta_modelo, False, "Hay más de 7 días seguidos sin registro.")
    if abs(delta) <= tol:
        return Desviacion(delta, delta_meta, delta_modelo, False, "El progreso está dentro de la tolerancia.")
    lado = "por encima" if delta > 0 else "por debajo"
    return Desviacion(delta, delta_meta, delta_modelo, True,
                      f"Tu tendencia va {abs(delta):.1f} kg {lado} del plan.")


@dataclass
class ComposicionReplaneacion:
    W0: float
    F0: float
    L0: float
    N: int
    aviso: str | None


def composicion_replaneacion(W_real: float, L_sim: float, N: int, x_u: int, perfil: Perfil) -> ComposicionReplaneacion:
    """W0' = W_real, L0' = L_sim, F0' = W0' − L0', N' = N − x_u."""
    N2 = N - x_u
    if N2 < 2:
        raise ErrorMotor("plazo_agotado", "El plan ya casi termina: crea un plan nuevo en lugar de re-planear.")
    F0 = W_real - L_sim
    aviso = None
    if F0 <= 0.05 * W_real:
        pct = grasa_deurenberg(perfil, W_real)
        F0 = pct / 100.0 * W_real
        aviso = "La grasa simulada era demasiado baja; se estimó de nuevo con el IMC."
    return ComposicionReplaneacion(W_real, F0, W_real - F0, N2, aviso)
