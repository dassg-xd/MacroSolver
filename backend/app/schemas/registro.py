"""Esquemas de los registros diarios y del calendario (HU-10 a HU-12).

Un registro solo se acepta entre la fecha de inicio del plan y hoy (o la fecha
meta, si ya pasó). Enviar ``null`` en calorías o peso borra el registro de ese día.
"""
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

KCAL_MAXIMAS = Decimal("10000")
PESO_MINIMO_KG = Decimal("30")
PESO_MAXIMO_KG = Decimal("300")
MINUTOS_MAXIMOS = 600
ACTIVIDADES_POR_DIA = 10

EstadoDia = Literal["registrado", "estimado", "futuro", "fuera_del_plan"]


class CaloriasRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date
    kcal: Decimal | None = Field(default=None, ge=0, le=KCAL_MAXIMAS)


class PesoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date
    peso_kg: Decimal | None = Field(default=None, ge=PESO_MINIMO_KG, le=PESO_MAXIMO_KG)


class ActividadDia(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actividad_id: int = Field(ge=1)
    minutos: int = Field(ge=1, le=MINUTOS_MAXIMOS)


class ActividadesRequest(BaseModel):
    """Reemplaza todas las actividades del día. Una lista vacía deja el día como descanso."""

    model_config = ConfigDict(extra="forbid")

    fecha: date
    actividades: list[ActividadDia] = Field(default_factory=list, max_length=ACTIVIDADES_POR_DIA)

    @field_validator("actividades")
    @classmethod
    def validar_total(cls, valor: list[ActividadDia]) -> list[ActividadDia]:
        if sum(a.minutos for a in valor) > 24 * 60:
            raise ValueError("Las actividades del día no pueden sumar más de 24 horas.")
        return valor


class ActividadCatalogo(BaseModel):
    id: int
    nombre: str
    tipo: str
    met: float


class ActividadRegistrada(BaseModel):
    actividad_id: int
    nombre: str
    tipo: str
    met: float
    minutos: int
    kcal_estimadas: float


class DiaCalendario(BaseModel):
    fecha: date
    dia_plan: int | None
    estado: EstadoDia
    kcal: float | None
    peso_kg: float | None
    actividades: list[ActividadRegistrada]
    kcal_ejercicio: float
    cumplido: bool | None


class CalendarioResponse(BaseModel):
    mes: str
    hoy: date
    plan_id: int
    fecha_inicio: date
    fecha_meta: date
    ingesta_objetivo_kcal: float
    banda_cumplimiento: float
    dias: list[DiaCalendario]


class CaloriasResponse(BaseModel):
    fecha: date
    kcal: float | None


class PesoResponse(BaseModel):
    fecha: date
    peso_kg: float | None


class ActividadesResponse(BaseModel):
    fecha: date
    actividades: list[ActividadRegistrada]
    kcal_ejercicio: float
