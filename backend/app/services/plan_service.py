"""Lógica de planeación: composición, viabilidad, vista previa y cálculo.

El motor numérico es puro; aquí se traduce entre fechas, perfiles y la base de
datos. La vista previa responde 200 aunque la meta no sea viable: los bloqueos
son parte de la respuesta, no errores de red.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Mapping

from macrosolver import (
    Composicion,
    ErrorMotor,
    Perfil,
    calcular_ingesta_meta,
    estimar_grasa,
    evaluar_viabilidad,
    imc,
    macros,
    meta_por_grasa,
    referencia_rk4,
    rango_ingesta,
    simular_composicion,
    tdee,
)
from macrosolver.constantes import (
    DEFICIT_MAXIMO,
    FRACCION_MASA_LIBRE_AVISO,
    MAX_ITER_SECANTE,
    TOL_SECANTE_KG,
    TOLERANCIA_REPLANEACION,
)
from macrosolver.viabilidad import ingesta_minima

from app.repositories.plan_repository import ErrorCrearPlan
from app.schemas.plan import DatosPlanRequest, EstimarComposicionRequest
from app.services.motor_adaptador import perfil_desde_plan, perfil_desde_usuario

IMC_MINIMO_META = 18.5
HORIZONTE_DIAS = 180

ADVERTENCIA_COMPOSICION = (
    "La composición corporal es una estimación aproximada, no una medición."
)
ADVERTENCIA_DEURENBERG = (
    "Se estimó la grasa con edad, sexo, peso y altura porque faltan medidas. "
    "Agrega cuello, cintura y cadera para una estimación más precisa."
)

FORMULAS = {
    "modelo": (
        "W = F + L; p(F) = C / (C + F); "
        "dF/dt = (1 − p) · B / ρF; dL/dt = p · B / ρL; B = I − TDEE(W)."
    ),
    "tdee": (
        "TDEE(W) = factor de actividad · (10·W + 6,25·altura − 5·edad + s), "
        "con s = 5 para hombres y −161 para mujeres."
    ),
    "euler": (
        "W(n+1) = W(n) + 1 día · (I − TDEE(W(n))), repartido entre grasa y "
        "masa libre con p(F)."
    ),
    "secante": (
        "Se busca la ingesta I tal que el peso del día N sea la meta, con "
        "tolerancia de 0,01 kg y salvaguarda por bisección."
    ),
    "macros": (
        "Proteína 2,2 g/kg de masa libre; grasa 25 % de las kcal; el resto, "
        "carbohidratos."
    ),
}


class ErrorPlan(Exception):
    """Error de dominio con mensaje en español y código estable."""

    def __init__(self, mensaje: str, status_code: int = 422, codigo: str = "plan_invalido") -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status_code = status_code
        self.codigo = codigo


# --------------------------------------------------------------------- redondeo
def _r(valor: float, decimales: int = 1) -> float:
    return round(float(valor), decimales)


def _composicion_dict(comp: Composicion, perfil: Perfil, peso: float) -> dict[str, Any]:
    return {
        "pct_grasa": _r(comp.pct_grasa),
        "grasa_inicial_kg": _r(comp.F0, 2),
        "masa_libre_inicial_kg": _r(comp.L0, 2),
        "metodo": comp.metodo,
        "imc": _r(imc(peso, perfil.altura_cm)),
    }


def _viabilidad_dict(via: Any, inicio: date, ingesta_viable: float | None = None) -> dict[str, Any]:
    fecha_viable = (
        inicio + timedelta(days=via.n_min_dias)
        if via.n_min_dias is not None
        else None
    )
    return {
        "viable": via.viable,
        "alcanzable": via.alcanzable,
        "n_min_dias": via.n_min_dias,
        "fecha_viable": fecha_viable,
        "ingesta_rapida_kcal": _r(via.i_rapida),
        "ingesta_viable_kcal": (
            _r(ingesta_viable) if ingesta_viable is not None else None
        ),
        "mensaje": via.mensaje,
    }


def _sensibilidad_dict(rango: Any) -> dict[str, Any]:
    return {
        "minimo_kcal": _r(rango.minimo),
        "maximo_kcal": _r(rango.maximo),
        "variantes": {nombre: _r(valor) for nombre, valor in rango.variantes.items()},
        "omitidas": list(rango.omitidas),
    }


def _macros_dict(valores: Any) -> dict[str, Any]:
    return {
        "proteina_g": _r(valores.proteina_g),
        "grasa_g": _r(valores.grasa_g),
        "carbohidratos_g": _r(valores.carbohidratos_g),
        "fraccion_grasa": _r(valores.fraccion_grasa, 2),
        "advertencia": valores.advertencia,
    }


def _curva_dict(tr: Any, tolerancia: float = TOLERANCIA_REPLANEACION) -> dict[str, Any]:
    dias = list(range(len(tr.W)))
    return {
        "dias": dias,
        "peso_kg": [_r(valor, 3) for valor in tr.W],
        "grasa_kg": [_r(valor, 3) for valor in tr.F],
        "masa_libre_kg": [_r(valor, 3) for valor in tr.L],
        "banda_inferior_kg": [_r(valor - tolerancia, 3) for valor in tr.W],
        "banda_superior_kg": [_r(valor + tolerancia, 3) for valor in tr.W],
    }


def _calculo_dict(
    perfil: Perfil,
    composicion: Composicion,
    viabilidad: Any,
    secante: Any,
    ingesta: float,
    N: int,
    sensibilidad: Any,
    inicio: date,
) -> dict[str, Any]:
    """Iteraciones de la Secante y error de Euler frente a Runge-Kutta 4."""
    euler = simular_composicion(composicion.F0, composicion.L0, perfil, ingesta, N)
    rk4 = referencia_rk4(composicion.F0, composicion.L0, perfil, ingesta, N)

    paso_rk = (len(rk4.W) - 1) / N if N else 1
    errores = [
        abs(euler.W[dia] - rk4.W[int(round(dia * paso_rk))])
        for dia in range(N + 1)
    ]

    return {
        "secante": {
            "tolerancia_kg": TOL_SECANTE_KG,
            "max_iteraciones": MAX_ITER_SECANTE,
            "raiz_kcal": _r(secante.raiz),
            "error_raiz_kg": _r(secante.f_raiz, 4),
            "iteraciones": [
                {
                    "k": paso.k,
                    "ingesta_kcal": _r(paso.ingesta),
                    "error_kg": _r(paso.f, 4),
                    "paso": paso.paso,
                }
                for paso in secante.historial
            ],
        },
        "euler": {
            "paso_dias": 1.0,
            "error_final_kg": _r(errores[-1], 4),
            "error_maximo_kg": _r(max(errores), 4),
        },
        "sensibilidad": _sensibilidad_dict(sensibilidad) if sensibilidad else None,
        "composicion": _composicion_dict(
            composicion, perfil, composicion.F0 + composicion.L0
        ),
        "viabilidad": _viabilidad_dict(viabilidad, inicio),
        "formulas": FORMULAS,
    }


def equivalente_en_grasa(comp: Composicion, perfil: Perfil, kg: float) -> dict[str, Any] | None:
    """Meta de peso para que los `kg` pedidos sean de grasa, o None si no es posible."""
    try:
        meta = meta_por_grasa(comp.F0, comp.L0, perfil.sexo, kg)
    except ErrorMotor:
        return None
    imc_meta = imc(meta.peso_meta_kg, perfil.altura_cm)
    return {
        "grasa_a_perder_kg": _r(kg, 2),
        "peso_meta_kg": _r(meta.peso_meta_kg, 1),
        "imc_meta": _r(imc_meta),
        "pct_grasa_final": _r(meta.pct_grasa_final),
        "segura": meta.segura and imc_meta >= IMC_MINIMO_META,
    }


def aviso_masa_libre(perdida: Mapping[str, float]) -> str | None:
    """Aviso cuando más de un tercio de la pérdida sería masa libre (Forbes)."""
    peso = perdida["peso_kg"]
    if peso <= 0 or perdida["masa_libre_kg"] / peso <= FRACCION_MASA_LIBRE_AVISO:
        return None
    pct = 100 * perdida["masa_libre_kg"] / peso
    return (
        f"De los {peso:.1f} kg que bajarías, se estima que solo "
        f"{perdida['grasa_kg']:.1f} kg serían grasa y {perdida['masa_libre_kg']:.1f} kg "
        f"({pct:.0f} %) masa libre, sobre todo músculo con su agua. Comer la proteína "
        "indicada y entrenar fuerza ayuda a conservar el músculo."
    )


# --------------------------------------------------------------------- casos de uso
def estimar_composicion(
    usuario: Mapping[str, Any],
    datos: EstimarComposicionRequest,
) -> dict[str, Any]:
    """HU-06: composición estimada sin crear un plan."""
    datos = datos if hasattr(datos, "peso_kg") else EstimarComposicionRequest(**dict(datos))
    perfil = perfil_desde_usuario(usuario)
    comp = estimar_grasa(
        perfil,
        float(datos.peso_kg),
        _float_o_none(datos.cuello_cm),
        _float_o_none(datos.cintura_cm),
        _float_o_none(datos.cadera_cm),
    )
    return {
        "pct_grasa": _r(comp.pct_grasa),
        "grasa_kg": _r(comp.F0, 2),
        "masa_libre_kg": _r(comp.L0, 2),
        "metodo": comp.metodo,
        "imc": _r(imc(float(datos.peso_kg), perfil.altura_cm)),
        "aviso": ADVERTENCIA_DEURENBERG if comp.metodo == "deurenberg" else None,
    }


def vista_previa(
    usuario: Mapping[str, Any],
    datos: DatosPlanRequest,
    *,
    perfil_fijo: Perfil | None = None,
    composicion: Composicion | None = None,
) -> dict[str, Any]:
    """HU-05 a HU-09: viabilidad, ingesta, macros, curva y cómo se calculó.

    perfil_fijo y composicion se usan al re-planear: el perfil es la copia del
    plan y la composición viene de la simulación, no de las medidas.
    """
    datos = datos if hasattr(datos, "fecha_inicio") else DatosPlanRequest(**dict(datos))
    perfil = perfil_fijo or perfil_desde_usuario(usuario)
    inicio = datos.fecha_inicio or date.today()
    N = datos.plazo_dias
    W0 = float(datos.peso_inicial_kg)

    comp = composicion or estimar_grasa(
        perfil,
        W0,
        _float_o_none(datos.cuello_cm),
        _float_o_none(datos.cintura_cm),
        _float_o_none(datos.cadera_cm),
    )

    # Meta en grasa: se traduce a peso con Forbes y sigue el mismo disparo.
    bloqueo_grasa: dict[str, str] | None = None
    grasa_a_perder: float | None = None
    if datos.tipo_meta == "grasa":
        grasa_a_perder = float(datos.grasa_a_perder_kg)
        try:
            meta_grasa = meta_por_grasa(comp.F0, comp.L0, perfil.sexo, grasa_a_perder)
        except ErrorMotor as error:
            bloqueo_grasa = {"codigo": "grasa_insuficiente", "mensaje": error.mensaje}
            W_meta = W0
        else:
            W_meta = round(meta_grasa.peso_meta_kg, 2)
            if not meta_grasa.segura:
                bloqueo_grasa = {
                    "codigo": "grasa_meta_muy_baja",
                    "mensaje": (
                        f"Perder {grasa_a_perder:.1f} kg de grasa te dejaría con "
                        f"{meta_grasa.pct_grasa_final:.1f} % de grasa; el mínimo "
                        f"seguro es {meta_grasa.pct_grasa_minimo:.0f} %. Elige una meta menor."
                    ),
                }
    else:
        W_meta = float(datos.peso_objetivo_kg)

    base: dict[str, Any] = {
        "puede_confirmar": False,
        "bloqueos": [],
        "advertencias": [ADVERTENCIA_COMPOSICION],
        "fecha_inicio": inicio,
        "fecha_meta": datos.fecha_meta,
        "plazo_dias": N,
        "composicion": _composicion_dict(comp, perfil, W0),
        "viabilidad": None,
        "ingesta_kcal": None,
        "macros": None,
        "curva": None,
        "perdida": None,
        "sensibilidad": None,
        "calculo": None,
        "equivalente_grasa": (
            equivalente_en_grasa(comp, perfil, W0 - W_meta)
            if datos.tipo_meta == "peso" and W_meta < W0
            else None
        ),
        "meta": {
            "tipo": datos.tipo_meta,
            "peso_objetivo_kg": _r(W_meta, 2),
            "grasa_a_perder_kg": _r(grasa_a_perder, 2) if grasa_a_perder is not None else None,
        },
    }

    if comp.metodo == "deurenberg" and composicion is None:
        base["advertencias"].append(ADVERTENCIA_DEURENBERG)

    if bloqueo_grasa:
        base["bloqueos"].append(bloqueo_grasa)
        base["viabilidad"] = _viabilidad_dict(
            _viabilidad_vacia(perfil, W0, mensaje=(
                "No se evaluó la viabilidad porque la meta de grasa no es posible o "
                "no es segura."
            )),
            inicio,
        )
        return base

    # 1. La meta debe ser una pérdida de peso.
    if W_meta >= W0:
        base["bloqueos"].append({
            "codigo": "meta_no_es_perdida",
            "mensaje": (
                "La meta debe ser menor que el peso inicial: el modelo solo "
                "planea pérdida de peso."
            ),
        })
        base["viabilidad"] = _viabilidad_dict(
            _viabilidad_vacia(perfil, W0, mensaje=(
                "No se evaluó la viabilidad porque la meta no es una pérdida "
                "de peso."
            )),
            inicio,
        )
        return base

    # 2. IMC de la meta por debajo del mínimo seguro.
    imc_meta = imc(W_meta, perfil.altura_cm)
    if imc_meta < IMC_MINIMO_META:
        base["bloqueos"].append({
            "codigo": "imc_bajo",
            "mensaje": (
                f"El peso meta da un IMC de {imc_meta:.1f}. El mínimo seguro "
                f"es {IMC_MINIMO_META:.1f}; ajusta la meta."
            ),
        })
        base["viabilidad"] = _viabilidad_dict(
            _viabilidad_vacia(
                perfil,
                W0,
                mensaje=(
                    "El peso meta no es seguro; ajusta la meta antes de "
                    "simular la viabilidad."
                ),
            ),
            inicio,
        )
        return base

    via = evaluar_viabilidad(comp.F0, comp.L0, perfil, W_meta, N)
    base["viabilidad"] = _viabilidad_dict(via, inicio)

    # 3. Ni con el déficit máximo se alcanza la meta.
    if not via.alcanzable:
        base["bloqueos"].append({
            "codigo": "meta_inalcanzable",
            "mensaje": via.mensaje,
        })
        return base

    # 4. Fuera del horizonte de 180 días.
    if via.n_min_dias is None or via.n_min_dias > HORIZONTE_DIAS:
        base["bloqueos"].append({
            "codigo": "fuera_de_horizonte",
            "mensaje": (
                "Con el déficit máximo permitido la meta no se alcanza en "
                f"{HORIZONTE_DIAS} días. Elige una meta más cercana o un plazo "
                "más largo."
            ),
        })
        return base

    # 5. La fecha pedida no alcanza, pero existe una fecha viable.
    if via.n_min_dias > N:
        ingesta_viable = _ingesta_viable(comp, perfil, W_meta, via)
        base["viabilidad"] = _viabilidad_dict(via, inicio, ingesta_viable)
        base["bloqueos"].append({
            "codigo": "plazo_no_viable",
            "mensaje": (
                f"La fecha pedida no alcanza: lo más pronto que se puede llegar "
                f"con seguridad es en {via.n_min_dias} días "
                f"({base['viabilidad']['fecha_viable']})."
            ),
        })
        return base

    # Cálculo completo.
    try:
        sec = calcular_ingesta_meta(comp.F0, comp.L0, perfil, N, W_meta, via.i_rapida)
        valores = macros(sec.raiz, comp.L0)
    except ErrorMotor as error:
        if error.codigo == "macros_imposibles":
            base["bloqueos"].append({"codigo": error.codigo, "mensaje": error.mensaje})
            return base
        raise

    I = sec.raiz
    tr = simular_composicion(comp.F0, comp.L0, perfil, I, N)
    sensibilidad = rango_ingesta(perfil, W0, comp.pct_grasa, N, W_meta, I)

    advertencias = list(base["advertencias"])
    if valores.advertencia:
        advertencias.append(valores.advertencia)
    deficit_inicial = tdee(W0, perfil) - I
    if deficit_inicial > 0.9 * DEFICIT_MAXIMO:
        advertencias.append(
            f"El déficit inicial ({deficit_inicial:.0f} kcal) está cerca del "
            "máximo permitido."
        )
    if I < ingesta_minima(W0, perfil) * 1.05:
        advertencias.append("La ingesta está cerca del mínimo seguro.")

    perdida = {
        "peso_kg": _r(W0 - tr.W[-1], 2),
        "grasa_kg": _r(comp.F0 - tr.F[-1], 2),
        "masa_libre_kg": _r(comp.L0 - tr.L[-1], 2),
    }
    # Con meta en grasa la tarjeta «Tu meta» ya explica el reparto.
    aviso_libre = aviso_masa_libre(perdida) if datos.tipo_meta == "peso" else None
    if aviso_libre:
        advertencias.append(aviso_libre)

    base.update({
        "puede_confirmar": True,
        "advertencias": advertencias,
        "ingesta_kcal": _r(I),
        "macros": _macros_dict(valores),
        "curva": _curva_dict(tr),
        "perdida": perdida,
        "sensibilidad": _sensibilidad_dict(sensibilidad),
        "calculo": _calculo_dict(perfil, comp, via, sec, I, N, sensibilidad, inicio),
    })
    return base


def crear_plan(
    usuario: Mapping[str, Any],
    datos: DatosPlanRequest,
    repositorio: Any,
    *,
    perfil_fijo: Perfil | None = None,
    composicion: Composicion | None = None,
    sexo: str | None = None,
) -> dict[str, Any]:
    """HU-05: recalcula en servidor y guarda el plan con la RPC transaccional."""
    previa = vista_previa(usuario, datos, perfil_fijo=perfil_fijo, composicion=composicion)
    if not previa["puede_confirmar"]:
        mensajes = " ".join(bloqueo["mensaje"] for bloqueo in previa["bloqueos"])
        raise ErrorPlan(
            mensajes or "No se puede confirmar el plan con estos datos.",
            422,
            "plan_bloqueado",
        )

    datos = datos if hasattr(datos, "fecha_inicio") else DatosPlanRequest(**dict(datos))
    perfil = perfil_fijo or perfil_desde_usuario(usuario)
    inicio = datos.fecha_inicio or date.today()
    N = datos.plazo_dias
    W0 = float(datos.peso_inicial_kg)
    # Con meta en grasa, el peso meta es el que calculó la vista previa.
    W_meta = float(previa["meta"]["peso_objetivo_kg"])
    comp = composicion or estimar_grasa(
        perfil,
        W0,
        _float_o_none(datos.cuello_cm),
        _float_o_none(datos.cintura_cm),
        _float_o_none(datos.cadera_cm),
    )

    try:
        fila = repositorio.crear(
            usuario["id"],
            {
                "fecha_inicio": inicio.isoformat(),
                "plazo_dias": N,
                "peso_inicial_kg": _r(W0, 2),
                "peso_objetivo_kg": _r(W_meta, 2),
                "ingesta_kcal": _r(previa["ingesta_kcal"]),
                "proteina_g": _r(previa["macros"]["proteina_g"]),
                "grasa_g": _r(previa["macros"]["grasa_g"]),
                "carbohidratos_g": _r(previa["macros"]["carbohidratos_g"]),
                "sexo": sexo or usuario["sexo"],
                "edad_anios": perfil.edad,
                "altura_cm": _r(perfil.altura_cm, 1),
                "factor_actividad": _r(perfil.f_act, 3),
                "cuello_cm": _float_o_none(datos.cuello_cm),
                "cintura_cm": _float_o_none(datos.cintura_cm),
                "cadera_cm": _float_o_none(datos.cadera_cm),
                "pct_grasa": _r(comp.pct_grasa),
                "grasa_inicial_kg": _r(comp.F0, 2),
                "masa_libre_inicial_kg": _r(comp.L0, 2),
                "metodo_grasa": comp.metodo,
                "tolerancia_kg": TOLERANCIA_REPLANEACION,
            },
        )
    except ErrorCrearPlan as error:
        raise ErrorPlan(str(error), 500, "plan_no_guardado") from error
    return _plan_dict(fila)


def obtener_activo(usuario: Mapping[str, Any], repositorio: Any) -> dict[str, Any]:
    fila = repositorio.buscar_activo(usuario["id"])
    if fila is None:
        raise ErrorPlan(
            "Todavía no tienes un plan activo. Crea uno para empezar.",
            404,
            "sin_plan_activo",
        )
    return _plan_dict(fila)


def calculo_activo(usuario: Mapping[str, Any], repositorio: Any) -> dict[str, Any]:
    """HU-09: cómo se calculó el plan activo, recalculado desde sus datos."""
    fila = repositorio.buscar_activo(usuario["id"])
    if fila is None:
        raise ErrorPlan(
            "Todavía no tienes un plan activo. Crea uno para ver su cálculo.",
            404,
            "sin_plan_activo",
        )

    perfil = perfil_desde_plan(fila)
    N = int(fila["plazo_dias"])
    W0 = float(fila["peso_inicial_kg"])
    W_meta = float(fila["peso_objetivo_kg"])
    comp = Composicion(
        pct_grasa=float(fila["pct_grasa"]),
        F0=float(fila["grasa_inicial_kg"]),
        L0=float(fila["masa_libre_inicial_kg"]),
        metodo=fila["metodo_grasa"],
    )
    inicio = _fecha(fila["fecha_inicio"])

    via = evaluar_viabilidad(comp.F0, comp.L0, perfil, W_meta, N)
    sec = calcular_ingesta_meta(comp.F0, comp.L0, perfil, N, W_meta, via.i_rapida)
    sensibilidad = rango_ingesta(perfil, W0, comp.pct_grasa, N, W_meta, sec.raiz)

    return _calculo_dict(
        perfil,
        comp,
        via,
        sec,
        float(fila["ingesta_kcal"]),
        N,
        sensibilidad,
        inicio,
    )


# --------------------------------------------------------------------- auxiliares
def _float_o_none(valor: Any) -> float | None:
    return None if valor is None else float(valor)


def _fecha(valor: Any) -> date:
    return valor if isinstance(valor, date) else date.fromisoformat(str(valor))


def _ingesta_viable(
    comp: Composicion,
    perfil: Perfil,
    W_meta: float,
    via: Any,
) -> float | None:
    if via.n_min_dias is None:
        return None
    try:
        return calcular_ingesta_meta(
            comp.F0, comp.L0, perfil, via.n_min_dias, W_meta, via.i_rapida
        ).raiz
    except ErrorMotor:
        return None


def _viabilidad_vacia(
    perfil: Perfil,
    W0: float,
    mensaje: str,
) -> Any:
    """Viabilidad informativa cuando un bloqueo evita simular la meta."""
    from macrosolver.viabilidad import Viabilidad, ingesta_rapida

    return Viabilidad(
        viable=False,
        alcanzable=False,
        i_rapida=ingesta_rapida(W0, perfil),
        n_min=None,
        n_min_dias=None,
        mensaje=mensaje,
    )


def _plan_dict(fila: Mapping[str, Any]) -> dict[str, Any]:
    inicio = _fecha(fila["fecha_inicio"])
    fecha_meta_raw = fila.get("fecha_meta")
    if fecha_meta_raw is None:
        fecha_meta_raw = (inicio + timedelta(days=int(fila["plazo_dias"]))).isoformat()
    fecha_meta = _fecha(fecha_meta_raw)
    plazo = int(fila["plazo_dias"])
    transcurridos = max(0, min(plazo, (date.today() - inicio).days))
    return {
        "id": int(fila["id"]),
        "fecha_inicio": inicio,
        "fecha_meta": fecha_meta,
        "plazo_dias": plazo,
        "peso_inicial_kg": _r(fila["peso_inicial_kg"], 2),
        "peso_objetivo_kg": _r(fila["peso_objetivo_kg"], 2),
        "ingesta_kcal": _r(fila["ingesta_kcal"]),
        "proteina_g": _r(fila["proteina_g"]),
        "grasa_g": _r(fila["grasa_g"]),
        "carbohidratos_g": _r(fila["carbohidratos_g"]),
        "composicion": {
            "pct_grasa": _r(fila["pct_grasa"]),
            "grasa_inicial_kg": _r(fila["grasa_inicial_kg"], 2),
            "masa_libre_inicial_kg": _r(fila["masa_libre_inicial_kg"], 2),
            "metodo": fila["metodo_grasa"],
            "imc": _r(
                imc(
                    float(fila["peso_inicial_kg"]),
                    float(fila["altura_cm"]),
                )
            ),
        },
        "tolerancia_kg": _r(fila.get("tolerancia_kg") or TOLERANCIA_REPLANEACION, 2),
        "estado": fila["estado"],
        "creado_en": fila["creado_en"],
        "dias_transcurridos": transcurridos,
        "dias_restantes": max(0, plazo - transcurridos),
    }
