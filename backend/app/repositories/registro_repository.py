"""Acceso a registro_calorias, registro_peso, registro_actividad y actividad_catalogo.

Calorías y peso tienen un índice único (plan_id, fecha), así que se guardan con
upsert. Las actividades de un día se reemplazan completas: se borran y se insertan.
"""
from datetime import date
from typing import Any, Sequence

from app.services.configSupabase import cliente_supabase


class RegistroRepository:
    # ---------------------------------------------------------------- lectura
    def catalogo(self) -> list[dict[str, Any]]:
        respuesta = (
            cliente_supabase.table("actividad_catalogo")
            .select("id, nombre, tipo, met")
            .order("id")
            .execute()
        )
        return respuesta.data or []

    def listar(self, plan_id: int, desde: date, hasta: date) -> dict[str, list[dict[str, Any]]]:
        """Registros del plan entre dos fechas (incluidas)."""

        def rango(tabla: str, columnas: str) -> list[dict[str, Any]]:
            respuesta = (
                cliente_supabase.table(tabla)
                .select(columnas)
                .eq("plan_id", plan_id)
                .gte("fecha", desde.isoformat())
                .lte("fecha", hasta.isoformat())
                .order("fecha")
                .execute()
            )
            return respuesta.data or []

        return {
            "calorias": rango("registro_calorias", "fecha, kcal"),
            "pesos": rango("registro_peso", "fecha, peso_kg"),
            "actividades": rango("registro_actividad", "fecha, actividad_id, minutos"),
        }

    def ultimo_peso_hasta(self, plan_id: int, fecha: date) -> float | None:
        respuesta = (
            cliente_supabase.table("registro_peso")
            .select("peso_kg")
            .eq("plan_id", plan_id)
            .lte("fecha", fecha.isoformat())
            .order("fecha", desc=True)
            .limit(1)
            .execute()
        )
        return float(respuesta.data[0]["peso_kg"]) if respuesta.data else None

    # ---------------------------------------------------------------- escritura
    def guardar_calorias(self, plan_id: int, fecha: date, kcal: float) -> None:
        cliente_supabase.table("registro_calorias").upsert(
            {"plan_id": plan_id, "fecha": fecha.isoformat(), "kcal": kcal},
            on_conflict="plan_id,fecha",
        ).execute()

    def borrar_calorias(self, plan_id: int, fecha: date) -> None:
        (
            cliente_supabase.table("registro_calorias")
            .delete()
            .eq("plan_id", plan_id)
            .eq("fecha", fecha.isoformat())
            .execute()
        )

    def guardar_peso(self, plan_id: int, fecha: date, peso_kg: float) -> None:
        cliente_supabase.table("registro_peso").upsert(
            {"plan_id": plan_id, "fecha": fecha.isoformat(), "peso_kg": peso_kg},
            on_conflict="plan_id,fecha",
        ).execute()

    def borrar_peso(self, plan_id: int, fecha: date) -> None:
        (
            cliente_supabase.table("registro_peso")
            .delete()
            .eq("plan_id", plan_id)
            .eq("fecha", fecha.isoformat())
            .execute()
        )

    def reemplazar_actividades(
        self, plan_id: int, fecha: date, actividades: Sequence[dict[str, int]]
    ) -> None:
        (
            cliente_supabase.table("registro_actividad")
            .delete()
            .eq("plan_id", plan_id)
            .eq("fecha", fecha.isoformat())
            .execute()
        )
        if actividades:
            cliente_supabase.table("registro_actividad").insert(
                [
                    {
                        "plan_id": plan_id,
                        "fecha": fecha.isoformat(),
                        "actividad_id": a["actividad_id"],
                        "minutos": a["minutos"],
                    }
                    for a in actividades
                ]
            ).execute()
