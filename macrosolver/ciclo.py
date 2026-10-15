"""Ciclo completo (seccion 5 del README): planeacion, adherencia, tendencia y re-planeacion."""
from __future__ import annotations

import numpy as np

from .metodos_numericos import calcular_ingesta_meta, euler, regresion_exponencial
from .modelo import Perfil, macros, tdee, tmb


def ejecutar_ciclo(p: Perfil, w0: float, w_obj: float, dias: int,
                   kcal_reales: dict, pesos: list, tolerancia_kg: float = 1.0) -> dict:
    """
    kcal_reales: {dia(1..): kcal consumidas ese dia}
    pesos:       [(dia, peso_kg), ...]  (dia 0 = peso inicial)
    """
    if dias < 2:
        raise ValueError("El plazo debe ser de al menos 2 dias.")
    if abs(w_obj - w0) < 0.1:
        raise ValueError("El peso objetivo debe diferir del peso inicial.")

    # 1) Planeacion: Secante + Euler (curva ideal)
    ingesta, hist = calcular_ingesta_meta(w0, w_obj, dias, p)
    ideal = euler(w0, ingesta, dias, p)

    # 2) Adherencia: Euler con las kcal reales (dias sin registro -> se asume el plan)
    kcal_reales = {int(d): float(k) for d, k in kcal_reales.items() if 1 <= int(d)}
    d_kcal = min(max(kcal_reales, default=0), dias)
    ing_real = [kcal_reales.get(d, ingesta) for d in range(1, dias + 1)]
    adher = euler(w0, ing_real, dias, p)

    # Retraso/adelanto: se extiende la simulacion hasta que cruza la meta
    extra = 180
    ing_ext = [kcal_reales.get(d, ingesta) for d in range(1, dias + extra + 1)]
    ext = euler(w0, ing_ext, dias + extra, p)
    sentido = np.sign(w_obj - w0)
    cruces = np.where(sentido * (ext - w_obj) >= 0)[0]
    dia_cruce = int(cruces[0]) if len(cruces) else None

    # 3) Seguimiento fisico: minimos cuadrados sobre los pesos reales
    pesos = sorted((int(d), float(w)) for d, w in pesos if 0 <= int(d) <= dias)
    C = A = proyectado = None
    if len(pesos) >= 2 and len({d for d, _ in pesos}) >= 2:
        C, A = regresion_exponencial([d for d, _ in pesos], [w for _, w in pesos])
        proyectado = C * np.exp(A * dias)

    # 4) Re-planeacion
    desviacion = None if proyectado is None else float(proyectado - w_obj)
    replanear = desviacion is not None and abs(desviacion) > tolerancia_kg
    nuevo = None
    if replanear:
        d_peso, w_actual = pesos[-1]
        restante = dias - d_peso
        if restante >= 1 and abs(w_obj - w_actual) >= 0.05:
            nueva_ing, _ = calcular_ingesta_meta(w_actual, w_obj, restante, p)
            nuevo = {
                "dia_inicio": d_peso, "peso_actual": w_actual, "dias_restantes": restante,
                "ingesta": nueva_ing,
                "curva": euler(w_actual, nueva_ing, restante, p),
                "macros": macros(nueva_ing, w_actual),
            }

    return {
        "perfil": p, "w0": w0, "w_obj": w_obj, "dias": dias, "tolerancia": tolerancia_kg,
        "ingesta": ingesta, "hist_secante": hist, "macros": macros(ingesta, w0),
        "ideal": ideal, "adher": adher, "d_kcal": d_kcal, "kcal_reales": kcal_reales,
        "dia_cruce": dia_cruce, "pesos": pesos, "C": C, "A": A,
        "proyectado": proyectado, "desviacion": desviacion,
        "replanear": replanear, "nuevo": nuevo,
        "tmb0": tmb(w0, p), "tdee0": tdee(w0, p),
    }


def advertencias(res: dict) -> list:
    av = []
    piso = 1500 if res["perfil"].sexo == "M" else 1200
    if res["ingesta"] < res["tmb0"]:
        av.append(f"La ingesta recomendada ({res['ingesta']:.0f} kcal) esta por debajo de tu TMB "
                  f"({res['tmb0']:.0f} kcal). Meta demasiado agresiva para el plazo.")
    elif res["ingesta"] < piso:
        av.append(f"La ingesta recomendada ({res['ingesta']:.0f} kcal) esta por debajo de {piso} kcal. "
                  "Considera ampliar el plazo.")
    if len(res["pesos"]) == 1:
        av.append("Solo hay 1 peso registrado: se necesitan al menos 2 para la regresion.")
    elif 2 <= len(res["pesos"]) < 3:
        av.append("Con solo 2 pesos la tendencia es poco confiable; registra mas semanas.")
    return av


def resumen(res: dict) -> str:
    """Resumen en texto del ciclo (para la consola)."""
    l = [f"TMB inicial: {res['tmb0']:.0f} kcal | TDEE inicial: {res['tdee0']:.0f} kcal",
         f"Ingesta recomendada (Secante): {res['ingesta']:.0f} kcal/dia -> "
         f"P {res['macros']['proteina_g']:.0f} g, G {res['macros']['grasa_g']:.0f} g, "
         f"C {res['macros']['carbohidratos_g']:.0f} g"]
    if res["C"] is not None:
        l.append(f"Tendencia real: Peso(x) = {res['C']:.2f}*e^({res['A']:.5f}*x) -> "
                 f"proyeccion dia {res['dias']}: {res['proyectado']:.2f} kg (meta {res['w_obj']} kg)")
    if res["nuevo"]:
        n = res["nuevo"]
        l.append(f"RE-PLANEACION: desde {n['peso_actual']:.1f} kg (dia {n['dia_inicio']}), "
                 f"{n['dias_restantes']} dias -> nueva ingesta {n['ingesta']:.0f} kcal/dia")
    else:
        l.append("Sin re-planeacion necesaria.")
    return "\n".join(l)
