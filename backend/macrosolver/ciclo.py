"""Orquestadores: lo que necesitan /plans/preview y /plans/active/seguimiento (sección 10).

El motor trabaja con índices de día (i = fecha − fecha_inicio). Convertir fechas
a índices y de vuelta es trabajo de la capa services del backend.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Mapping, Sequence

from .composicion import Composicion, estimar_grasa
from .constantes import DEFICIT_MAXIMO, TOLERANCIA_REPLANEACION
from .energia import tdee
from .estadisticas import gasto_ejercicio_dia
from .macros import Macros, macros
from .modelo import simular_composicion
from .secante import calcular_ingesta_meta
from .seguimiento import (Desviacion, Llegada, Tendencia, calcular_tendencia, evaluar_replaneacion,
                          llegada_estimada, simular_adherencia)
from .sensibilidad import RangoIngesta, rango_ingesta
from .tipos import ErrorMotor, PasoSecante, Perfil
from .viabilidad import Viabilidad, evaluar_viabilidad, ingesta_minima


@dataclass
class VistaPrevia:
    composicion: Composicion
    viabilidad: Viabilidad
    ingesta: float | None = None
    macros: Macros | None = None
    historial_secante: list[PasoSecante] = field(default_factory=list)
    curva_ideal: dict[str, list[float]] | None = None    # W, F, L por día
    rango: RangoIngesta | None = None
    advertencias: list[str] = field(default_factory=list)

    def a_dict(self) -> dict:
        return asdict(self)


def calcular_vista_previa(perfil: Perfil, W0: float, W_meta: float, N: int, cuello: float | None = None,
                          cintura: float | None = None, cadera: float | None = None,
                          F0: float | None = None, con_sensibilidad: bool = True) -> VistaPrevia:
    """Composición → viabilidad → Secante sobre Euler → macros → curva ideal → rango.

    Si se pasa F0 (re-planeación), se usa en lugar de estimar la grasa con medidas.
    """
    if N < 2:
        raise ErrorMotor("plazo_invalido", "El plazo debe ser de al menos 2 días.")
    if F0 is None:
        comp = estimar_grasa(perfil, W0, cuello, cintura, cadera)
    else:
        comp = Composicion(pct_grasa=100.0 * F0 / W0, F0=F0, L0=W0 - F0, metodo="re-planeación")

    via = evaluar_viabilidad(comp.F0, comp.L0, perfil, W_meta, N)
    res = VistaPrevia(composicion=comp, viabilidad=via,
                      advertencias=["La composición corporal es una estimación aproximada."])
    if not via.viable:
        return res

    sec = calcular_ingesta_meta(comp.F0, comp.L0, perfil, N, W_meta, via.i_rapida)
    I = sec.raiz
    res.ingesta = I
    res.historial_secante = sec.historial
    res.macros = macros(I, comp.L0)
    if res.macros.advertencia:
        res.advertencias.append(res.macros.advertencia)
    deficit = tdee(W0, perfil) - I
    if deficit > 0.9 * DEFICIT_MAXIMO:
        res.advertencias.append(f"El déficit inicial ({deficit:.0f} kcal) está cerca del máximo permitido.")
    if I < ingesta_minima(W0, perfil) * 1.05:
        res.advertencias.append("La ingesta está cerca del mínimo seguro.")

    tr = simular_composicion(comp.F0, comp.L0, perfil, I, N)
    res.curva_ideal = {"W": tr.W, "F": tr.F, "L": tr.L}
    if con_sensibilidad:
        res.rango = rango_ingesta(perfil, W0, comp.pct_grasa, N, W_meta, I)
    return res


@dataclass
class Seguimiento:
    curva_ideal: list[float]
    curva_adherencia: list[float]
    estimado: list[bool]
    curva_ejercicio: list[float] | None
    pesos_reales: dict[int, float]
    tendencia: Tendencia | None
    llegada: Llegada
    desviacion: Desviacion

    def a_dict(self) -> dict:
        return asdict(self)


def calcular_seguimiento(perfil: Perfil, F0: float, L0: float, ingesta_plan: float, N: int, W_meta: float,
                         dia_actual: int, calorias: Mapping[int, float], pesos: Mapping[int, float],
                         actividades: Mapping[int, Sequence[tuple[float, int]]] | None = None,
                         tol: float = TOLERANCIA_REPLANEACION) -> Seguimiento:
    """Recalcula todo desde el día 0 con los registros actuales (sección 6.3).

    pesos debe incluir el día 0 (peso_inicial_kg). actividades: {día: [(MET, minutos)]}.
    """
    ideal = simular_composicion(F0, L0, perfil, ingesta_plan, N).W
    adh = simular_adherencia(F0, L0, perfil, ingesta_plan, N, calorias)
    curva_ej = None
    if actividades:
        E = {i: gasto_ejercicio_dia(a) for i, a in actividades.items()}
        curva_ej = simular_adherencia(F0, L0, perfil, ingesta_plan, N, calorias, ejercicio=E).W
    tend = calcular_tendencia(pesos) if len(set(pesos)) >= 2 else None
    lleg = llegada_estimada(F0, L0, perfil, ingesta_plan, N, calorias, W_meta)
    con_registro = set(calorias) | set(pesos) | set(actividades or {})
    desv = evaluar_replaneacion(pesos, ideal, adh.W, W_meta, N, dia_actual, con_registro, tol)
    return Seguimiento(ideal, adh.W, adh.estimado, curva_ej, dict(pesos), tend, lleg, desv)

