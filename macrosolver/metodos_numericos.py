"""Metodos numericos (seccion 4 del README): Euler, Secante y Minimos Cuadrados."""
from __future__ import annotations

import numpy as np

from .modelo import KCAL_POR_KG, Perfil, tdee


# ---------------------------------------------------------------- 4.1 Euler
def euler(w0: float, ingesta, dias: int, p: Perfil) -> np.ndarray:
    """
    W_{i+1} = W_i + (Ingesta - TDEE(W_i)) / 7700      (h = 1 dia)

    `ingesta` puede ser un numero (kcal constantes) o una lista de `dias` valores.
    Devuelve un arreglo de longitud dias+1 (peso del dia 0 al dia `dias`).
    """
    ing = np.full(dias, float(ingesta)) if np.isscalar(ingesta) else np.asarray(ingesta, float)
    if len(ing) != dias:
        raise ValueError("La lista de ingestas debe tener exactamente `dias` valores.")
    w = np.empty(dias + 1)
    w[0] = w0
    for i in range(dias):
        w[i + 1] = w[i] + (ing[i] - tdee(w[i], p)) / KCAL_POR_KG
    return w


# -------------------------------------------------------------- 4.2 Secante
def secante(f, x0: float, x1: float, tol: float = 1e-6, max_iter: int = 50):
    """
    x_{n+1} = x_n - f(x_n) * (x_n - x_{n-1}) / (f(x_n) - f(x_{n-1}))

    Devuelve (raiz, historial[(n, x, f(x))]).
    """
    f0, f1 = f(x0), f(x1)
    hist = [(0, x0, f0), (1, x1, f1)]
    for n in range(2, max_iter + 2):
        if abs(f1) < tol:
            return x1, hist
        if f1 == f0:
            raise ArithmeticError("La Secante se estanco (f(x_n) == f(x_n-1)).")
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        x0, f0 = x1, f1
        x1, f1 = x2, f(x2)
        hist.append((n, x1, f1))
    if abs(f1) < tol:
        return x1, hist
    raise RuntimeError("La Secante no convergio.")


def calcular_ingesta_meta(w0: float, w_obj: float, dias: int, p: Perfil):
    """Ingesta diaria que lleva de w0 a w_obj en `dias` dias (Euler + Secante)."""
    def f(x):
        return euler(w0, x, dias, p)[-1] - w_obj
    return secante(f, 2000.0, 1500.0)


# ------------------------------------------------ 4.3 Minimos cuadrados
def regresion_exponencial(xs, ys):
    """Ajusta y = C * e^(A x) linealizando con ln(y). Devuelve (C, A)."""
    x = np.asarray(xs, float)
    y = np.asarray(ys, float)
    n = len(x)
    if n < 2:
        raise ValueError("Se necesitan al menos 2 pesos registrados.")
    if np.any(y <= 0):
        raise ValueError("Los pesos deben ser positivos.")
    ly = np.log(y)
    den = n * np.sum(x ** 2) - np.sum(x) ** 2
    if abs(den) < 1e-12:
        raise ValueError("Los pesos deben estar en al menos 2 dias distintos.")
    A = (n * np.sum(x * ly) - np.sum(x) * np.sum(ly)) / den
    a0 = (np.sum(ly) - A * np.sum(x)) / n
    return float(np.exp(a0)), float(A)
