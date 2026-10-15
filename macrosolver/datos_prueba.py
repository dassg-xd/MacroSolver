"""Datos de prueba: generador de usuarios simulados y lectura de datos escritos a mano."""
from __future__ import annotations

import re

import numpy as np

from .metodos_numericos import euler
from .modelo import Perfil


def generar_datos_prueba(ingesta_plan: float, p: Perfil, w0: float, dias_sim: int = 28,
                         desvio_kcal: float = 300.0, ruido_kcal: float = 250.0,
                         ruido_peso: float = 0.25, cada_dias: int = 7, seed: int | None = 42):
    """Simula a un usuario: come (plan + desvio + ruido) y se pesa cada `cada_dias`.
    Devuelve ({dia: kcal}, [(dia, peso)])."""
    rng = np.random.default_rng(seed)
    kcal = np.clip(ingesta_plan + desvio_kcal + rng.normal(0, ruido_kcal, dias_sim), 800, None).round()
    w = euler(w0, kcal, dias_sim, p)
    dias_peso = list(range(0, dias_sim + 1, cada_dias))
    pesos = [(d, float(w[d] + (0 if d == 0 else rng.normal(0, ruido_peso)))) for d in dias_peso]
    return {d + 1: float(k) for d, k in enumerate(kcal)}, pesos


def parsear_pares(texto: str):
    """Lee lineas 'dia, valor' (separadas por coma, punto y coma, tab o espacio).
    Devuelve ([(dia:int, valor:float)], [mensajes de error])."""
    pares, errores = [], []
    for n, linea in enumerate((texto or "").splitlines(), 1):
        linea = linea.split("#")[0].strip()
        if not linea:
            continue
        partes = [t for t in re.split(r"[,;\t ]+", linea) if t]
        try:
            if len(partes) != 2:
                raise ValueError
            pares.append((int(float(partes[0])), float(partes[1])))
        except ValueError:
            errores.append(f"Linea {n} ignorada (se esperaba 'dia, valor'): {linea!r}")
    return pares, errores
