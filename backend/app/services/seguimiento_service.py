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


# --------------------------------------------------------------------- re-planeación
def _preparar_replaneacion(
    d: DatosSeguimiento, fecha_meta: date | None
) -> tuple[DatosPlanRequest, Composicion, dict[str, Any]]:
    """W0' = último peso real, L0' = masa libre simulada ese día, N' = días restantes (5.9)."""
    x_u = max(d.pesos)
    if x_u == 0:
        raise ErrorPlan(
            "Registra al menos un peso después del día de inicio para poder re-planear.",
            422, "sin_pesos",
        )
    W_real = d.pesos[x_u]
    if W_real <= d.W_meta:
        raise ErrorPlan(
            "Tu último peso ya alcanzó la meta. Crea un plan nuevo con otra meta.",
            422, "meta_alcanzada",
        )
    adherencia = simular_adherencia(d.F0, d.L0, d.perfil, d.ingesta, d.N, d.calorias)
    cr = composicion_replaneacion(W_real, adherencia.L[x_u], d.N, x_u, d.perfil)
    comp = Composicion(
        pct_grasa=100.0 * cr.F0 / cr.W0, F0=cr.F0, L0=cr.L0, metodo=d.plan["metodo_grasa"]
    )
    try:
        datos = DatosPlanRequest(
            peso_inicial_kg=round(W_real, 2),
            peso_objetivo_kg=d.W_meta,
            fecha_inicio=d.fecha(x_u),
            fecha_meta=fecha_meta or d.meta,
        )
    except ValidationError as error:
        mensaje = str(error.errors()[0]["msg"]).removeprefix("Value error, ")
        raise ErrorPlan(mensaje, 422, "replaneacion_invalida") from error

    seg = calcular_seguimiento(
        d.perfil, d.F0, d.L0, d.ingesta, d.N, d.W_meta, d.dia_actual,
        d.calorias, d.pesos, None, tol=d.tolerancia,
    )
    info = {
        "sugerida": seg.desviacion.sugerir,
        "motivo": seg.desviacion.motivo,
        "dia_ultimo_peso": x_u,
        "fecha_ultimo_peso": d.fecha(x_u),
        "peso_real_kg": _r(W_real),
        "aviso_composicion": cr.aviso,
        "actual": {
            "ingesta_kcal": _r(d.ingesta, 1),
            "macros": {
                "proteina_g": _r(d.plan["proteina_g"], 1),
                "grasa_g": _r(d.plan["grasa_g"], 1),
                "carbohidratos_g": _r(d.plan["carbohidratos_g"], 1),
                "fraccion_grasa": _r(9.0 * float(d.plan["grasa_g"]) / d.ingesta, 2),
                "advertencia": None,
            },
            "dias_restantes": d.N - x_u,
        },
    }
    return datos, comp, info


def vista_previa_replaneacion(
    usuario: Mapping[str, Any], fecha_meta: date | None, planes: Any, registros: Any
) -> dict[str, Any]:
    """HU-13: plan propuesto junto al actual. No guarda nada."""
    d = _cargar(usuario, planes, registros)
    datos, comp, info = _preparar_replaneacion(d, fecha_meta)
    previa = plan_service.vista_previa(usuario, datos, perfil_fijo=d.perfil, composicion=comp)
    previa["replaneacion"] = info
    return previa


def replanear(
    usuario: Mapping[str, Any], fecha_meta: date | None, planes: Any, registros: Any
) -> dict[str, Any]:
    """HU-14: crea el plan encadenado; el anterior queda inactivo y en el historial."""
    d = _cargar(usuario, planes, registros)
    datos, comp, _ = _preparar_replaneacion(d, fecha_meta)
    nuevo = plan_service.crear_plan(
        usuario, datos, planes, perfil_fijo=d.perfil, composicion=comp, sexo=d.plan["sexo"]
    )
    _copiar_registros(d, int(nuevo["id"]), datos.fecha_inicio, registros)
    return nuevo


def _copiar_registros(d: DatosSeguimiento, plan_nuevo: int, desde: date, registros: Any) -> None:
    """Los registros desde el nuevo día 0 pasan al plan nuevo para no perderlos."""
    hasta = min(d.hoy, d.meta)
    if hasta < desde:
        return
    filas = registros.listar(d.plan_id, desde, hasta)
    for r in filas["calorias"]:
        registros.guardar_calorias(plan_nuevo, _fecha(r["fecha"]), float(r["kcal"]))
    por_fecha: dict[date, list[dict[str, int]]] = {}
    for r in filas["actividades"]:
        por_fecha.setdefault(_fecha(r["fecha"]), []).append(
            {"actividad_id": int(r["actividad_id"]), "minutos": int(r["minutos"])}
        )
    for fecha, lista in por_fecha.items():
        registros.reemplazar_actividades(plan_nuevo, fecha, lista)


# --------------------------------------------------------------------- estadísticas
def estadisticas(usuario: Mapping[str, Any], planes: Any, registros: Any) -> dict[str, Any]:
    """HU-20: adherencia, peso promedio y ejercicio por semana (domingo a sábado)."""
    d = _cargar(usuario, planes, registros)
    semanas = estadisticas_semanales(
        d.inicio, d.dia_actual, d.ingesta, d.calorias, d.pesos, d.actividades
    )
    registrados = len(d.calorias)
    cumplidos = sum(
        1 for k in d.calorias.values() if abs(k - d.ingesta) <= ADHERENCIA_BANDA * d.ingesta
    )
    peso_actual = d.pesos[max(d.pesos)]
    return {
        "plan_id": d.plan_id,
        "banda_cumplimiento": ADHERENCIA_BANDA,
        "resumen": {
            "dias_transcurridos": d.dia_actual + 1,
            "dias_registrados": registrados,
            "dias_cumplidos": cumplidos,
            "adherencia_pct": _r(100 * cumplidos / registrados, 1) if registrados else None,
            "promedio_kcal": _r(sum(d.calorias.values()) / registrados, 0) if registrados else None,
            "objetivo_kcal": _r(d.ingesta, 1),
            "peso_inicial_kg": _r(d.W0),
            "peso_actual_kg": _r(peso_actual),
            "cambio_kg": _r(peso_actual - d.W0),
            "sesiones": sum(len(a) for a in d.actividades.values()),
            "minutos": sum(m for a in d.actividades.values() for _, m in a),
        },
        "semanas": [
            {
                "inicio": s.inicio, "fin": s.fin,
                "dias_registrados": s.dias_registrados, "dias_cumplidos": s.dias_cumplidos,
                "adherencia_pct": _r(100 * s.adherencia, 1) if s.adherencia is not None else None,
                "peso_promedio_kg": _r(s.peso_promedio),
                "variacion_kg": _r(s.variacion),
                "sesiones": s.sesiones, "minutos": s.minutos,
                "kcal_ejercicio": _r(s.kcal_ejercicio, 0), "parcial": s.parcial,
            }
            for s in semanas
        ],
    }


# --------------------------------------------------------------------- historial
def historial(usuario: Mapping[str, Any], planes: Any, registros: Any) -> list[dict[str, Any]]:
    """HU-08: planes del usuario, del más reciente al más antiguo."""
    resultado = []
    for plan in planes.listar(usuario["id"]):
        inicio, meta = registro_service.limites_plan(plan)
        ultimo = registros.ultimo_peso_hasta(int(plan["id"]), meta)
        inicial = float(plan["peso_inicial_kg"])
        resultado.append({
            "id": int(plan["id"]),
            "estado": plan["estado"],
            "plan_previo_id": plan.get("plan_previo_id"),
            "fecha_inicio": inicio,
            "fecha_meta": meta,
            "plazo_dias": int(plan["plazo_dias"]),
            "peso_inicial_kg": _r(inicial),
            "peso_objetivo_kg": _r(plan["peso_objetivo_kg"]),
            "ingesta_kcal": _r(plan["ingesta_kcal"], 1),
            "ultimo_peso_kg": _r(ultimo),
            "cambio_kg": _r(ultimo - inicial) if ultimo is not None else None,
            "creado_en": plan["creado_en"],
        })
    return resultado


# --------------------------------------------------------------------- guía
# Reglas fijas (HU-15): porcentaje de la ingesta del día en cada comida.
REPARTO_COMIDAS: dict[int, list[tuple[str, int]]] = {
    3: [("Desayuno", 30), ("Almuerzo", 40), ("Cena", 30)],
    4: [("Desayuno", 25), ("Almuerzo", 35), ("Merienda", 15), ("Cena", 25)],
    5: [("Desayuno", 20), ("Media mañana", 10), ("Almuerzo", 35), ("Merienda", 10), ("Cena", 25)],
}

CONSEJOS = [
    "Reparte la proteína en todas las comidas: ayuda a conservar el músculo y da saciedad.",
    "Planea las comidas del día siguiente; improvisar es lo que más desvía las calorías.",
    "Registra lo que comes el mismo día. Un día sin registro se simula con la ingesta del plan.",
    "Pésate en las mismas condiciones (al despertar, después del baño) para que los pesos sean comparables.",
    "Un día fuera del objetivo no arruina el plan: importa el promedio de la semana.",
    "Si entrenas fuerza, mantenla durante el déficit: reduce la pérdida de masa libre.",
]


def guia(usuario: Mapping[str, Any], comidas: int, planes: Any) -> dict[str, Any]:
    """HU-15: macros del plan activo repartidos en 3, 4 o 5 comidas."""
    if comidas not in REPARTO_COMIDAS:
        raise ErrorPlan("El número de comidas debe ser 3, 4 o 5.", 422, "comidas_invalidas")
    plan = registro_service._plan_activo(usuario, planes)
    ingesta = float(plan["ingesta_kcal"])
    macros = {k: float(plan[k]) for k in ("proteina_g", "grasa_g", "carbohidratos_g")}
    return {
        "comidas": comidas,
        "ingesta_kcal": _r(ingesta, 0),
        **{k: _r(v, 0) for k, v in macros.items()},
        "reparto": [
            {
                "nombre": nombre,
                "porcentaje": pct,
                "kcal": _r(ingesta * pct / 100, 0),
                **{k: _r(v * pct / 100, 0) for k, v in macros.items()},
            }
            for nombre, pct in REPARTO_COMIDAS[comidas]
        ],
        "consejos": CONSEJOS,
    }
