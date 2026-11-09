"""Registros diarios (calorías, peso, actividad) y vista mensual del calendario.

Reglas:
- Solo se registra en el plan activo, entre su fecha de inicio y hoy
  (o la fecha meta, si ya pasó). No se registran días futuros.
- Calorías y peso: un valor por día; ``None`` borra el registro.
- Actividades: la lista enviada reemplaza la del día; vacía = descanso.
- Un día sin calorías registradas y ya pasado se muestra como «estimado»: el
  seguimiento lo simula con la ingesta del plan (sección 6.3).
- Un día con calorías se marca cumplido si queda dentro de ±10 % de la ingesta.
"""
from __future__ import annotations

import calendar
import re
from datetime import date, timedelta
from typing import Any, Mapping

from macrosolver import gasto_ejercicio_dia
from macrosolver.constantes import ADHERENCIA_BANDA

from app.schemas.registro import ActividadesRequest, CaloriasRequest, PesoRequest
from app.services.plan_service import ErrorPlan

_PATRON_MES = re.compile(r"^(\d{4})-(\d{2})$")


def hoy() -> date:
    """Fecha de hoy; las pruebas la reemplazan para no depender del reloj."""
    return date.today()


# --------------------------------------------------------------------- auxiliares
def _fecha(valor: Any) -> date:
    return valor if isinstance(valor, date) else date.fromisoformat(str(valor)[:10])


def _plan_activo(usuario: Mapping[str, Any], planes: Any) -> dict[str, Any]:
    plan = planes.buscar_activo(usuario["id"])
    if plan is None:
        raise ErrorPlan(
            "Todavía no tienes un plan activo. Crea uno para empezar a registrar.",
            404,
            "sin_plan_activo",
        )
    return plan


def limites_plan(plan: Mapping[str, Any]) -> tuple[date, date]:
    inicio = _fecha(plan["fecha_inicio"])
    return inicio, inicio + timedelta(days=int(plan["plazo_dias"]))


def dia_del_plan(plan: Mapping[str, Any], fecha: date) -> int | None:
    """Índice i = fecha − fecha_inicio que usa el motor, o None si cae fuera del plan."""
    inicio, meta = limites_plan(plan)
    if fecha < inicio or fecha > meta:
        return None
    return (fecha - inicio).days


def fecha_del_dia(plan: Mapping[str, Any], dia: int) -> date:
    """Inversa de dia_del_plan."""
    return limites_plan(plan)[0] + timedelta(days=dia)


def validar_fecha_registro(plan: Mapping[str, Any], fecha: date) -> None:
    inicio, meta = limites_plan(plan)
    if fecha < inicio:
        raise ErrorPlan(
            f"El plan empezó el {inicio.isoformat()}; no puedes registrar días anteriores.",
            422,
            "fecha_antes_del_plan",
        )
    if fecha > meta:
        raise ErrorPlan(
            f"El plan terminó el {meta.isoformat()}; no puedes registrar días posteriores.",
            422,
            "fecha_despues_del_plan",
        )
    if fecha > hoy():
        raise ErrorPlan("No puedes registrar días futuros.", 422, "fecha_futura")


def _kcal_ejercicio(actividades: list[tuple[float, int]], peso_kg: float) -> float:
    """kcal ≈ W · Σ (MET − 1)·horas: el gasto extra que usa el modelo (5.12)."""
    return round(peso_kg * gasto_ejercicio_dia(actividades), 1)


def _catalogo_por_id(registros: Any) -> dict[int, dict[str, Any]]:
    return {int(a["id"]): a for a in registros.catalogo()}


def _actividad_registrada(item: Mapping[str, Any], cat: Mapping[str, Any], peso_kg: float) -> dict[str, Any]:
    met = float(cat["met"])
    minutos = int(item["minutos"])
    return {
        "actividad_id": int(item["actividad_id"]),
        "nombre": cat["nombre"],
        "tipo": cat["tipo"],
        "met": met,
        "minutos": minutos,
        "kcal_estimadas": _kcal_ejercicio([(met, minutos)], peso_kg),
    }


def _peso_referencia(plan: Mapping[str, Any], registros: Any, fecha: date) -> float:
    ultimo = registros.ultimo_peso_hasta(int(plan["id"]), fecha)
    return ultimo if ultimo is not None else float(plan["peso_inicial_kg"])


# --------------------------------------------------------------------- casos de uso
def catalogo_actividades(registros: Any) -> list[dict[str, Any]]:
    return [
        {"id": int(a["id"]), "nombre": a["nombre"], "tipo": a["tipo"], "met": float(a["met"])}
        for a in registros.catalogo()
    ]


def guardar_calorias(usuario: Mapping[str, Any], datos: CaloriasRequest, planes: Any, registros: Any) -> dict[str, Any]:
    plan = _plan_activo(usuario, planes)
    validar_fecha_registro(plan, datos.fecha)
    if datos.kcal is None:
        registros.borrar_calorias(int(plan["id"]), datos.fecha)
        return {"fecha": datos.fecha, "kcal": None}
    kcal = round(float(datos.kcal), 1)
    registros.guardar_calorias(int(plan["id"]), datos.fecha, kcal)
    return {"fecha": datos.fecha, "kcal": kcal}


def guardar_peso(usuario: Mapping[str, Any], datos: PesoRequest, planes: Any, registros: Any) -> dict[str, Any]:
    plan = _plan_activo(usuario, planes)
    validar_fecha_registro(plan, datos.fecha)
    if datos.fecha == _fecha(plan["fecha_inicio"]):
        raise ErrorPlan(
            "El peso del día de inicio es el peso inicial del plan y no se cambia aquí.",
            422,
            "peso_inicial_fijo",
        )
    if datos.peso_kg is None:
        registros.borrar_peso(int(plan["id"]), datos.fecha)
        return {"fecha": datos.fecha, "peso_kg": None}
    peso = round(float(datos.peso_kg), 2)
    registros.guardar_peso(int(plan["id"]), datos.fecha, peso)
    return {"fecha": datos.fecha, "peso_kg": peso}


def guardar_actividades(
    usuario: Mapping[str, Any], datos: ActividadesRequest, planes: Any, registros: Any
) -> dict[str, Any]:
    plan = _plan_activo(usuario, planes)
    validar_fecha_registro(plan, datos.fecha)
    cat = _catalogo_por_id(registros)
    desconocidas = sorted({a.actividad_id for a in datos.actividades} - set(cat))
    if desconocidas:
        raise ErrorPlan(
            "La actividad elegida no existe en el catálogo.", 422, "actividad_inexistente"
        )
    lista = [{"actividad_id": a.actividad_id, "minutos": a.minutos} for a in datos.actividades]
    registros.reemplazar_actividades(int(plan["id"]), datos.fecha, lista)

    peso = _peso_referencia(plan, registros, datos.fecha)
    actividades = [_actividad_registrada(a, cat[a["actividad_id"]], peso) for a in lista]
    return {
        "fecha": datos.fecha,
        "actividades": actividades,
        "kcal_ejercicio": round(sum(a["kcal_estimadas"] for a in actividades), 1),
    }


def _mes(mes: str | None) -> tuple[date, date, str]:
    if mes is None:
        h = hoy()
        anio, numero = h.year, h.month
    else:
        coincidencia = _PATRON_MES.match(mes)
        if not coincidencia:
            raise ErrorPlan("El mes debe tener la forma AAAA-MM.", 422, "mes_invalido")
        anio, numero = int(coincidencia.group(1)), int(coincidencia.group(2))
        if not 1 <= numero <= 12 or not 2000 <= anio <= 2100:
            raise ErrorPlan("El mes no es válido.", 422, "mes_invalido")
    ultimo = calendar.monthrange(anio, numero)[1]
    return date(anio, numero, 1), date(anio, numero, ultimo), f"{anio:04d}-{numero:02d}"


def calendario(usuario: Mapping[str, Any], mes: str | None, planes: Any, registros: Any) -> dict[str, Any]:
    plan = _plan_activo(usuario, planes)
    primero, ultimo, etiqueta = _mes(mes)
    plan_id = int(plan["id"])
    inicio, meta = limites_plan(plan)
    ingesta = float(plan["ingesta_kcal"])
    h = hoy()

    datos = registros.listar(plan_id, primero, ultimo)
    calorias = {_fecha(r["fecha"]): float(r["kcal"]) for r in datos["calorias"]}
    pesos = {_fecha(r["fecha"]): float(r["peso_kg"]) for r in datos["pesos"]}
    pesos.setdefault(inicio, float(plan["peso_inicial_kg"]))
    actividades: dict[date, list[Mapping[str, Any]]] = {}
    for r in datos["actividades"]:
        actividades.setdefault(_fecha(r["fecha"]), []).append(r)
    cat = _catalogo_por_id(registros) if actividades else {}

    # Peso vigente al empezar el mes, para estimar el gasto de las actividades.
    peso_vigente = registros.ultimo_peso_hasta(plan_id, primero - timedelta(days=1))
    if peso_vigente is None:
        peso_vigente = float(plan["peso_inicial_kg"])

    dias = []
    d = primero
    while d <= ultimo:
        if d in pesos and inicio <= d <= meta:
            peso_vigente = pesos[d]
        indice = dia_del_plan(plan, d)
        kcal = calorias.get(d)
        if indice is None:
            estado = "fuera_del_plan"
        elif d > h:
            estado = "futuro"
        elif kcal is not None:
            estado = "registrado"
        else:
            estado = "estimado"

        registradas = [
            _actividad_registrada(a, cat[int(a["actividad_id"])], peso_vigente)
            for a in actividades.get(d, [])
            if int(a["actividad_id"]) in cat
        ]
        dias.append(
            {
                "fecha": d,
                "dia_plan": indice,
                "estado": estado,
                "kcal": kcal,
                "peso_kg": pesos.get(d) if indice is not None else None,
                "actividades": registradas,
                "kcal_ejercicio": round(sum(a["kcal_estimadas"] for a in registradas), 1),
                "cumplido": None if kcal is None else abs(kcal - ingesta) <= ADHERENCIA_BANDA * ingesta,
            }
        )
        d += timedelta(days=1)

    return {
        "mes": etiqueta,
        "hoy": h,
        "plan_id": plan_id,
        "fecha_inicio": inicio,
        "fecha_meta": meta,
        "ingesta_objetivo_kcal": round(ingesta, 1),
        "banda_cumplimiento": ADHERENCIA_BANDA,
        "dias": dias,
    }
