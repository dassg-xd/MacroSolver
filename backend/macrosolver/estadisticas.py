"""Estadísticas semanales, de domingo a sábado (5.10)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Mapping, Sequence

from .constantes import ADHERENCIA_BANDA


@dataclass
class Semana:
    inicio: date
    fin: date
    dias_registrados: int
    dias_cumplidos: int
    adherencia: float | None        # cumplidos / registrados
    peso_promedio: float | None
    variacion: float | None         # P̄_s − P̄_(s−1)
    sesiones: int
    minutos: int
    kcal_ejercicio: float           # aproximado
    parcial: bool


def _domingo(d: date) -> date:
    return d - timedelta(days=(d.weekday() + 1) % 7)   # weekday(): lunes = 0


def estadisticas_semanales(fecha_inicio: date, dia_actual: int, ingesta_plan: float,
                           calorias: Mapping[int, float], pesos: Mapping[int, float],
                           actividades: Mapping[int, Sequence[tuple[float, int]]] | None = None) -> list[Semana]:
    """actividades: {día: [(MET, minutos), ...]}. Devuelve las semanas de la más antigua a la actual."""
    actividades = actividades or {}
    hoy = fecha_inicio + timedelta(days=dia_actual)
    semanas: list[Semana] = []
    d = _domingo(fecha_inicio)
    previo = None
    ultimo_peso = pesos.get(0)
    while d <= hoy:
        fin = d + timedelta(days=6)
        idx = [(d + timedelta(days=k) - fecha_inicio).days for k in range(7)]
        idx = [i for i in idx if 0 <= i <= dia_actual]
        reg = [i for i in idx if i in calorias]
        cumplidos = sum(1 for i in reg if abs(calorias[i] - ingesta_plan) <= ADHERENCIA_BANDA * ingesta_plan)
        ps = [pesos[i] for i in idx if i in pesos]
        prom = sum(ps) / len(ps) if ps else None
        sesiones = minutos = 0
        kcal = 0.0
        for i in idx:
            if i in pesos:
                ultimo_peso = pesos[i]
            for met, mins in actividades.get(i, ()):
                sesiones += 1
                minutos += mins
                if ultimo_peso:
                    kcal += ultimo_peso * (met - 1.0) * mins / 60.0
        semanas.append(Semana(
            inicio=d, fin=fin, dias_registrados=len(reg), dias_cumplidos=cumplidos,
            adherencia=(cumplidos / len(reg)) if reg else None, peso_promedio=prom,
            variacion=(prom - previo) if (prom is not None and previo is not None) else None,
            sesiones=sesiones, minutos=minutos, kcal_ejercicio=kcal, parcial=fin >= hoy))
        if prom is not None:
            previo = prom
        d += timedelta(days=7)
    return semanas


def gasto_ejercicio_dia(actividades_dia: Sequence[tuple[float, int]]) -> float:
    """E_i = Σ (MET_j − 1)·horas_j, el término que entra en el balance (5.12)."""
    return sum((met - 1.0) * mins / 60.0 for met, mins in actividades_dia)
