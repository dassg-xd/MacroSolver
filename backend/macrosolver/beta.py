"""Compatibilidad con la beta (commit f1088b4, `macrosolver` 0.3.0-beta).

Conserva la API pública de la beta para que sus 6 pruebas (V5) sigan en verde:
`Perfil` ("M"/"F", factor_actividad), `euler` (modelo lineal de 7700 kcal/kg),
`secante` sin salvaguarda, `calcular_ingesta_meta(w0, w_obj, dias, p)`,
`regresion_exponencial` que devuelve (C, A), `ejecutar_ciclo`, `generar_datos_prueba`
y `parsear_pares`. Es Python puro: la beta usaba numpy, aquí se devuelven listas.

El sistema nuevo NO usa este módulo; usa `calcular_vista_previa` y
`calcular_seguimiento` (modelo de dos compartimentos, sección 5 del documento v0.5).
"""
from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass

from . import seguimiento as _seg
from .constantes import RHO_SIMPLE

KCAL_POR_KG = RHO_SIMPLE

FACTORES_ACTIVIDAD = {
    "Sedentario (1.2)": 1.2,
    "Ligera (1.375)": 1.375,
    "Moderada (1.55)": 1.55,
    "Alta (1.725)": 1.725,
    "Muy alta (1.9)": 1.9,
}


@dataclass
class Perfil:
    sexo: str            # "M" o "F"
    edad: float
    altura_cm: float
    factor_actividad: float


def tmb(peso_kg: float, p: Perfil) -> float:
    base = 10 * peso_kg + 6.25 * p.altura_cm - 5 * p.edad
    return base + 5 if p.sexo == "M" else base - 161


def tdee(peso_kg: float, p: Perfil) -> float:
    return tmb(peso_kg, p) * p.factor_actividad


def macros(calorias: float, peso_kg: float) -> dict:
    """Regla de la beta (2 g por kg de peso total). El sistema nuevo usa 2,2 g por kg magro."""
    proteina = 2.0 * peso_kg
    grasa = 0.25 * calorias / 9.0
    carbo = max(0.0, (calorias - proteina * 4 - grasa * 9) / 4.0)
    return {"proteina_g": proteina, "grasa_g": grasa, "carbohidratos_g": carbo}


def euler(w0: float, ingesta, dias: int, p: Perfil) -> list[float]:
    """W_(i+1) = W_i + (I_i − TDEE(W_i)) / 7700, h = 1 día. Equivale a `euler_simple`."""
    if isinstance(ingesta, (int, float)):
        ing = [float(ingesta)] * dias
    else:
        ing = [float(x) for x in ingesta]
    if len(ing) != dias:
        raise ValueError("La lista de ingestas debe tener exactamente `dias` valores.")
    w = [float(w0)]
    for i in range(dias):
        w.append(w[-1] + (ing[i] - tdee(w[-1], p)) / KCAL_POR_KG)
    return w


def secante(f, x0: float, x1: float, tol: float = 1e-6, max_iter: int = 50):
    """Secante sin salvaguarda de la beta. Devuelve (raiz, [(n, x, f(x))])."""
    f0, f1 = f(x0), f(x1)
    hist = [(0, x0, f0), (1, x1, f1)]
    for n in range(2, max_iter + 2):
        if abs(f1) < tol:
            return x1, hist
        if f1 == f0:
            raise ArithmeticError("La Secante se estancó (f(x_n) == f(x_n-1)).")
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        x0, f0 = x1, f1
        x1, f1 = x2, f(x2)
        hist.append((n, x1, f1))
    if abs(f1) < tol:
        return x1, hist
    raise RuntimeError("La Secante no convergió.")


def calcular_ingesta_meta(w0: float, w_obj: float, dias: int, p: Perfil):
    def f(x):
        return euler(w0, x, dias, p)[-1] - w_obj
    return secante(f, 2000.0, 1500.0)


def regresion_exponencial(xs, ys) -> tuple[float, float]:
    t = _seg.regresion_exponencial([float(x) for x in xs], [float(y) for y in ys])
    return t.C, t.A


def ejecutar_ciclo(p: Perfil, w0: float, w_obj: float, dias: int, kcal_reales: dict, pesos: list,
                   tolerancia_kg: float = 1.0) -> dict:
    """Ciclo de la beta. Ojo: aquí kcal_reales usa días desde 1 (convención vieja)."""
    if dias < 2:
        raise ValueError("El plazo debe ser de al menos 2 dias.")
    if abs(w_obj - w0) < 0.1:
        raise ValueError("El peso objetivo debe diferir del peso inicial.")

    ingesta, hist = calcular_ingesta_meta(w0, w_obj, dias, p)
    ideal = euler(w0, ingesta, dias, p)

    kcal_reales = {int(d): float(k) for d, k in kcal_reales.items() if 1 <= int(d)}
    d_kcal = min(max(kcal_reales, default=0), dias)
    adher = euler(w0, [kcal_reales.get(d, ingesta) for d in range(1, dias + 1)], dias, p)

    extra = 180
    ext = euler(w0, [kcal_reales.get(d, ingesta) for d in range(1, dias + extra + 1)], dias + extra, p)
    sentido = math.copysign(1.0, w_obj - w0)
    dia_cruce = next((i for i, w in enumerate(ext) if sentido * (w - w_obj) >= 0), None)

    pesos = sorted((int(d), float(w)) for d, w in pesos if 0 <= int(d) <= dias)
    C = A = proyectado = None
    if len(pesos) >= 2 and len({d for d, _ in pesos}) >= 2:
        C, A = regresion_exponencial([d for d, _ in pesos], [w for _, w in pesos])
        proyectado = C * math.exp(A * dias)

    desviacion = None if proyectado is None else float(proyectado - w_obj)
    replanear = desviacion is not None and abs(desviacion) > tolerancia_kg
    nuevo = None
    if replanear:
        d_peso, w_actual = pesos[-1]
        restante = dias - d_peso
        if restante >= 1 and abs(w_obj - w_actual) >= 0.05:
            nueva_ing, _ = calcular_ingesta_meta(w_actual, w_obj, restante, p)
            nuevo = {"dia_inicio": d_peso, "peso_actual": w_actual, "dias_restantes": restante,
                     "ingesta": nueva_ing, "curva": euler(w_actual, nueva_ing, restante, p),
                     "macros": macros(nueva_ing, w_actual)}

    return {"perfil": p, "w0": w0, "w_obj": w_obj, "dias": dias, "tolerancia": tolerancia_kg,
            "ingesta": ingesta, "hist_secante": hist, "macros": macros(ingesta, w0),
            "ideal": ideal, "adher": adher, "d_kcal": d_kcal, "kcal_reales": kcal_reales,
            "dia_cruce": dia_cruce, "pesos": pesos, "C": C, "A": A,
            "proyectado": proyectado, "desviacion": desviacion,
            "replanear": replanear, "nuevo": nuevo,
            "tmb0": tmb(w0, p), "tdee0": tdee(w0, p)}


def generar_datos_prueba(ingesta_plan: float, p: Perfil, w0: float, dias_sim: int = 28,
                         desvio_kcal: float = 300.0, ruido_kcal: float = 250.0,
                         ruido_peso: float = 0.25, cada_dias: int = 7, seed: int | None = 42):
    """Usuario simulado. Usa `random` en lugar de numpy: con la misma semilla los números cambian."""
    rng = random.Random(seed)
    kcal = [round(max(800.0, ingesta_plan + desvio_kcal + (rng.gauss(0, ruido_kcal) if ruido_kcal else 0.0)))
            for _ in range(dias_sim)]
    w = euler(w0, kcal, dias_sim, p)
    pesos = [(d, float(w[d] + (0 if d == 0 or not ruido_peso else rng.gauss(0, ruido_peso))))
             for d in range(0, dias_sim + 1, cada_dias)]
    return {d + 1: float(k) for d, k in enumerate(kcal)}, pesos


def parsear_pares(texto: str):
    """Lee líneas 'dia, valor'. Devuelve ([(dia, valor)], [errores])."""
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
