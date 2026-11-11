"""Esquemas de seguimiento, re-planeación, estadísticas, historial y guía (HU-08, HU-11 a HU-15, HU-20)."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.plan import MacrosResponse, VistaPreviaResponse


# ----------------------------------------------------------------- seguimiento
class PesoReal(BaseModel):
    dia: int
    fecha: date
    peso_kg: float


class TendenciaResponse(BaseModel):
    c: float
    a: float
    r2: float
    n: int
    tasa_semanal_pct: float
    curva: list[float]


class LlegadaResponse(BaseModel):
    dia: int | None
    fecha: date | None
    retraso_dias: int | None
    mensaje: str


class DesviacionResponse(BaseModel):
    delta_kg: float | None
    delta_meta_kg: float | None
    delta_modelo_kg: float | None
    sugerir: bool
    motivo: str


class ResumenHoy(BaseModel):
    fecha: date
    dia_plan: int
    dias_restantes: int
    kcal: float | None
    objetivo_kcal: float
    ultimo_peso_kg: float
    peso_ideal_kg: float


class SeguimientoResponse(BaseModel):
    plan_id: int
    fecha_inicio: date
    fecha_meta: date
    plazo_dias: int
    dia_actual: int
    peso_objetivo_kg: float
    tolerancia_kg: float
    dias: list[int]
    curva_ideal: list[float]
    curva_adherencia: list[float]
    estimado: list[bool]
    curva_ejercicio: list[float] | None
    pesos: list[PesoReal]
    tendencia: TendenciaResponse | None
    llegada: LlegadaResponse
    desviacion: DesviacionResponse
    hoy: ResumenHoy


# ----------------------------------------------------------------- re-planeación
class ReplanearRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Por defecto se conserva la fecha meta del plan; se envía otra para aceptar la fecha viable.
    fecha_meta: date | None = None


class PlanActualResumen(BaseModel):
    ingesta_kcal: float
    macros: MacrosResponse
    dias_restantes: int


class DatosReplaneacion(BaseModel):
    sugerida: bool
    motivo: str
    dia_ultimo_peso: int
    fecha_ultimo_peso: date
    peso_real_kg: float
    aviso_composicion: str | None
    actual: PlanActualResumen


class ReplaneacionPreviaResponse(VistaPreviaResponse):
    replaneacion: DatosReplaneacion


# ----------------------------------------------------------------- estadísticas
class SemanaResponse(BaseModel):
    inicio: date
    fin: date
    dias_registrados: int
    dias_cumplidos: int
    adherencia_pct: float | None
    peso_promedio_kg: float | None
    variacion_kg: float | None
    sesiones: int
    minutos: int
    kcal_ejercicio: float
    parcial: bool


class ResumenEstadisticas(BaseModel):
    dias_transcurridos: int
    dias_registrados: int
    dias_cumplidos: int
    adherencia_pct: float | None
    promedio_kcal: float | None
    objetivo_kcal: float
    peso_inicial_kg: float
    peso_actual_kg: float
    cambio_kg: float
    sesiones: int
    minutos: int


class EstadisticasResponse(BaseModel):
    plan_id: int
    banda_cumplimiento: float
    resumen: ResumenEstadisticas
    semanas: list[SemanaResponse]


# ----------------------------------------------------------------- historial
class PlanHistorial(BaseModel):
    id: int
    estado: str
    plan_previo_id: int | None
    fecha_inicio: date
    fecha_meta: date
    plazo_dias: int
    peso_inicial_kg: float
    peso_objetivo_kg: float
    ingesta_kcal: float
    ultimo_peso_kg: float | None
    cambio_kg: float | None
    creado_en: datetime


# ----------------------------------------------------------------- guía
class ComidaGuia(BaseModel):
    nombre: str
    porcentaje: int
    kcal: float
    proteina_g: float
    grasa_g: float
    carbohidratos_g: float


class GuiaResponse(BaseModel):
    comidas: int = Field(ge=3, le=5)
    ingesta_kcal: float
    proteina_g: float
    grasa_g: float
    carbohidratos_g: float
    reparto: list[ComidaGuia]
    consejos: list[str]
