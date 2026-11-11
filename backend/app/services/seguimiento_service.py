"""Seguimiento, re-planeación, estadísticas, historial y guía del plan.

El motor trabaja con índices de día (i = fecha − fecha_inicio). Aquí se leen los
registros de la base, se convierten a índices, se llama al motor y se devuelven
las series ya calculadas para que el frontend solo dibuje (sección 10).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Mapping

from pydantic import ValidationError

from macrosolver import (Composicion, Perfil, calcular_seguimiento, composicion_replaneacion,
                         estadisticas_semanales, simular_adherencia)
from macrosolver.constantes import ADHERENCIA_BANDA, TOLERANCIA_REPLANEACION

from app.schemas.plan import DatosPlanRequest
from app.services import plan_service, registro_service
from app.services.motor_adaptador import perfil_desde_plan
from app.services.plan_service import ErrorPlan

_fecha = registro_service._fecha


# --------------------------------------------------------------------- datos
class DatosSeguimiento:
    """Plan activo y sus registros convertidos a índices de día."""

    def __init__(self, plan: Mapping[str, Any], registros: Any) -> None:
        self.plan = plan
        self.plan_id = int(plan["id"])
        self.inicio, self.meta = registro_service.limites_plan(plan)
        self.N = int(plan["plazo_dias"])
        self.perfil: Perfil = perfil_desde_plan(plan)
        self.W0 = float(plan["peso_inicial_kg"])
        self.F0 = float(plan["grasa_inicial_kg"])
        self.L0 = float(plan.get("masa_libre_inicial_kg") or self.W0 - self.F0)
        self.W_meta = float(plan["peso_objetivo_kg"])
        self.ingesta = float(plan["ingesta_kcal"])
        self.tolerancia = float(plan.get("tolerancia_kg") or TOLERANCIA_REPLANEACION)
        self.hoy = registro_service.hoy()
        self.dia_actual = max(0, min(self.N, (self.hoy - self.inicio).days))

        hasta = min(self.hoy, self.meta)
        filas = (
            registros.listar(self.plan_id, self.inicio, hasta)
            if hasta >= self.inicio
            else {"calorias": [], "pesos": [], "actividades": []}
        )
        self.calorias = {self.dia(r["fecha"]): float(r["kcal"]) for r in filas["calorias"]}
        self.pesos = {self.dia(r["fecha"]): float(r["peso_kg"]) for r in filas["pesos"]}
        self.pesos[0] = self.W0          # el día 0 siempre es el peso inicial del plan
        self.actividades: dict[int, list[tuple[float, int]]] = {}
        if filas["actividades"]:
            met = {int(a["id"]): float(a["met"]) for a in registros.catalogo()}
            for r in filas["actividades"]:
                if int(r["actividad_id"]) in met:
                    self.actividades.setdefault(self.dia(r["fecha"]), []).append(
                        (met[int(r["actividad_id"])], int(r["minutos"]))
                    )

    def dia(self, fecha: Any) -> int:
        return (_fecha(fecha) - self.inicio).days

    def fecha(self, dia: int) -> date:
        return self.inicio + timedelta(days=dia)


def _cargar(usuario: Mapping[str, Any], planes: Any, registros: Any) -> DatosSeguimiento:
    return DatosSeguimiento(registro_service._plan_activo(usuario, planes), registros)


def _r(valor: float | None, decimales: int = 2) -> float | None:
    return None if valor is None else round(float(valor), decimales)


# --------------------------------------------------------------------- seguimiento
def seguimiento(usuario: Mapping[str, Any], planes: Any, registros: Any) -> dict[str, Any]:
    """HU-11 a HU-13: curvas, tendencia, llegada estimada y sugerencia de re-planeación."""
    d = _cargar(usuario, planes, registros)
    seg = calcular_seguimiento(
        d.perfil, d.F0, d.L0, d.ingesta, d.N, d.W_meta, d.dia_actual,
        d.calorias, d.pesos, d.actividades or None, tol=d.tolerancia,
    )
    tendencia = None
    if seg.tendencia is not None:
        t = seg.tendencia
        tendencia = {
            "c": _r(t.C, 4), "a": round(t.A, 7), "r2": _r(t.r2, 4), "n": t.n,
            "tasa_semanal_pct": _r(100 * t.tasa_semanal, 2),
            "curva": [_r(t.evaluar(i), 3) for i in range(d.N + 1)],
        }
    ll, dv = seg.llegada, seg.desviacion
    ultimo = max(d.pesos)
    return {
        "plan_id": d.plan_id,
        "fecha_inicio": d.inicio,
        "fecha_meta": d.meta,
        "plazo_dias": d.N,
        "dia_actual": d.dia_actual,
        "peso_objetivo_kg": _r(d.W_meta),
        "tolerancia_kg": _r(d.tolerancia),
        "dias": list(range(d.N + 1)),
        "curva_ideal": [_r(w, 3) for w in seg.curva_ideal],
        "curva_adherencia": [_r(w, 3) for w in seg.curva_adherencia],
        "estimado": seg.estimado,
        "curva_ejercicio": [_r(w, 3) for w in seg.curva_ejercicio] if seg.curva_ejercicio else None,
        "pesos": [
            {"dia": i, "fecha": d.fecha(i), "peso_kg": _r(p)} for i, p in sorted(d.pesos.items())
        ],
        "tendencia": tendencia,
        "llegada": {
            "dia": ll.dia,
            "fecha": d.fecha(ll.dia) if ll.dia is not None else None,
            "retraso_dias": ll.retraso,
            "mensaje": ll.mensaje,
        },
        "desviacion": {
            "delta_kg": _r(dv.delta), "delta_meta_kg": _r(dv.delta_meta),
            "delta_modelo_kg": _r(dv.delta_modelo), "sugerir": dv.sugerir, "motivo": dv.motivo,
        },
        "hoy": {
            "fecha": d.hoy,
            "dia_plan": d.dia_actual,
            "dias_restantes": d.N - d.dia_actual,
            "kcal": d.calorias.get(d.dia_actual) if d.hoy <= d.meta else None,
            "objetivo_kcal": _r(d.ingesta, 1),
            "ultimo_peso_kg": _r(d.pesos[ultimo]),
            "peso_ideal_kg": _r(seg.curva_ideal[d.dia_actual]),
        },
    }
