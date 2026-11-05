"""Acceso a la tabla plan.

La confirmación usa la función PostgreSQL ``crear_plan`` (migración 03) para
desactivar el plan anterior e insertar el nuevo en una sola transacción. El
cliente REST de Supabase no puede abrir transacciones por sí mismo.
"""
from typing import Any, Mapping

from postgrest import APIError

from app.services.configSupabase import cliente_supabase

# La RPC recibe los nombres con prefijo p_ para no confundirlos con columnas.
_PARAMETROS_RPC = {
    "fecha_inicio": "p_fecha_inicio",
    "plazo_dias": "p_plazo_dias",
    "peso_inicial_kg": "p_peso_inicial_kg",
    "peso_objetivo_kg": "p_peso_objetivo_kg",
    "ingesta_kcal": "p_ingesta_kcal",
    "proteina_g": "p_proteina_g",
    "grasa_g": "p_grasa_g",
    "carbohidratos_g": "p_carbohidratos_g",
    "sexo": "p_sexo",
    "edad_anios": "p_edad_anios",
    "altura_cm": "p_altura_cm",
    "factor_actividad": "p_factor_actividad",
    "cuello_cm": "p_cuello_cm",
    "cintura_cm": "p_cintura_cm",
    "cadera_cm": "p_cadera_cm",
    "pct_grasa": "p_pct_grasa",
    "grasa_inicial_kg": "p_grasa_inicial_kg",
    "masa_libre_inicial_kg": "p_masa_libre_inicial_kg",
    "metodo_grasa": "p_metodo_grasa",
    "tolerancia_kg": "p_tolerancia_kg",
}

_MENSAJE_MIGRACION = (
    "No se pudo guardar el plan porque falta la función crear_plan en la base "
    "de datos. Aplica backend/sql/03_plan_v0.04.sql y vuelve a intentarlo."
)


class ErrorCrearPlan(Exception):
    """La base de datos no pudo guardar el plan de forma transaccional."""


class PlanRepository:
    def buscar_activo(self, usuario_id: int) -> dict[str, Any] | None:
        respuesta = (
            cliente_supabase.table("plan")
            .select("*")
            .eq("usuario_id", usuario_id)
            .eq("estado", "activo")
            .limit(1)
            .execute()
        )
        return respuesta.data[0] if respuesta.data else None

    def crear(self, usuario_id: int, plan: Mapping[str, Any]) -> dict[str, Any]:
        parametros = {
            _PARAMETROS_RPC[campo]: valor
            for campo, valor in plan.items()
            if campo in _PARAMETROS_RPC
        }
        parametros["p_usuario_id"] = usuario_id

        try:
            respuesta = cliente_supabase.rpc("crear_plan", parametros).execute()
        except APIError as error:
            if _es_funcion_inexistente(error):
                raise ErrorCrearPlan(_MENSAJE_MIGRACION) from error
            raise ErrorCrearPlan(
                "La base de datos rechazó el plan. Revisa los datos e intenta "
                "de nuevo."
            ) from error

        datos = respuesta.data
        if isinstance(datos, list):
            datos = datos[0] if datos else None
        if not datos:
            raise ErrorCrearPlan("La base de datos no devolvió el plan creado.")
        return datos


def _es_funcion_inexistente(error: APIError) -> bool:
    codigo = getattr(error, "code", None)
    if codigo in ("PGRST202", "42883"):
        return True
    mensaje = str(getattr(error, "message", "")) or str(error)
    return "crear_plan" in mensaje and "not find" in mensaje.lower()
