"""Esquemas de la planeación (HU-05 a HU-09).

La vista previa nunca responde error por reglas de negocio: devuelve 200 con
``puede_confirmar: false`` y la lista de ``bloqueos``. Los errores 422 se
reservan para datos inválidos (fechas, pesos o medidas incoherentes).
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

META_MINIMA_KG = Decimal("30")
META_MAXIMA_KG = Decimal("300")
PLAZO_MINIMO_DIAS = 2
PLAZO_MAXIMO_DIAS = 730

MetodoGrasa = Literal["marina", "deurenberg"]


class DatosPlanRequest(BaseModel):
    """Entrada compartida por la vista previa y la confirmación."""

    model_config = ConfigDict(extra="forbid")

    peso_inicial_kg: Decimal = Field(ge=META_MINIMA_KG, le=META_MAXIMA_KG)
    peso_objetivo_kg: Decimal = Field(ge=META_MINIMA_KG, le=META_MAXIMA_KG)
    fecha_inicio: date | None = None
    fecha_meta: date
    cuello_cm: Decimal | None = Field(default=None, ge=20, le=250)
    cintura_cm: Decimal | None = Field(default=None, ge=30, le=250)
    cadera_cm: Decimal | None = Field(default=None, ge=30, le=250)

    @model_validator(mode="after")
    def validar_fechas(self) -> "DatosPlanRequest":
        hoy = date.today()
        inicio = self.fecha_inicio or hoy

        if inicio > hoy:
            raise ValueError("La fecha de inicio no puede ser futura.")
        if self.fecha_meta <= inicio:
            raise ValueError("La fecha meta debe ser posterior a la fecha de inicio.")

        plazo = (self.fecha_meta - inicio).days
        if plazo < PLAZO_MINIMO_DIAS:
            raise ValueError(
                f"El plazo debe ser de al menos {PLAZO_MINIMO_DIAS} días."
            )
        if plazo > PLAZO_MAXIMO_DIAS:
            raise ValueError(
                f"El plazo no puede superar {PLAZO_MAXIMO_DIAS} días."
            )

        self.fecha_inicio = inicio
        return self

    @property
    def plazo_dias(self) -> int:
        assert self.fecha_inicio is not None
        return (self.fecha_meta - self.fecha_inicio).days


class EstimarComposicionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    peso_kg: Decimal = Field(ge=META_MINIMA_KG, le=META_MAXIMA_KG)
    cuello_cm: Decimal | None = Field(default=None, ge=20, le=250)
    cintura_cm: Decimal | None = Field(default=None, ge=30, le=250)
    cadera_cm: Decimal | None = Field(default=None, ge=30, le=250)


class ComposicionResponse(BaseModel):
    pct_grasa: float
    grasa_inicial_kg: float
    masa_libre_inicial_kg: float
    metodo: MetodoGrasa
    imc: float


class EstimacionComposicionResponse(BaseModel):
    pct_grasa: float
    grasa_kg: float
    masa_libre_kg: float
    metodo: MetodoGrasa
    imc: float
    aviso: str | None = None


class Bloqueo(BaseModel):
    codigo: str
    mensaje: str


class ViabilidadResponse(BaseModel):
    viable: bool
    alcanzable: bool
    n_min_dias: int | None
    fecha_viable: date | None
    ingesta_rapida_kcal: float
    ingesta_viable_kcal: float | None = None
    mensaje: str


class MacrosResponse(BaseModel):
    proteina_g: float
    grasa_g: float
    carbohidratos_g: float
    fraccion_grasa: float
    advertencia: str | None = None


class CurvaResponse(BaseModel):
    dias: list[int]
    peso_kg: list[float]
    grasa_kg: list[float]
    masa_libre_kg: list[float]
    banda_inferior_kg: list[float]
    banda_superior_kg: list[float]


class EquivalenteGrasaResponse(BaseModel):
    """Meta de peso con la que los kg pedidos serían todos de grasa (Forbes)."""

    grasa_a_perder_kg: float
    peso_meta_kg: float
    imc_meta: float
    pct_grasa_final: float
    segura: bool


class PerdidaResponse(BaseModel):
    peso_kg: float
    grasa_kg: float
    masa_libre_kg: float


class SensibilidadResponse(BaseModel):
    minimo_kcal: float
    maximo_kcal: float
    variantes: dict[str, float]
    omitidas: list[str]


class PasoSecanteResponse(BaseModel):
    k: int
    ingesta_kcal: float
    error_kg: float
    paso: str


class CalculoSecanteResponse(BaseModel):
    tolerancia_kg: float
    max_iteraciones: int
    raiz_kcal: float
    error_raiz_kg: float
    iteraciones: list[PasoSecanteResponse]


class CalculoEulerResponse(BaseModel):
    paso_dias: float
    error_final_kg: float
    error_maximo_kg: float


class FormulasResponse(BaseModel):
    modelo: str
    tdee: str
    euler: str
    secante: str
    macros: str


class CalculoResponse(BaseModel):
    secante: CalculoSecanteResponse
    euler: CalculoEulerResponse
    sensibilidad: SensibilidadResponse | None
    composicion: ComposicionResponse
    viabilidad: ViabilidadResponse
    formulas: FormulasResponse


class VistaPreviaResponse(BaseModel):
    puede_confirmar: bool
    bloqueos: list[Bloqueo]
    advertencias: list[str]
    fecha_inicio: date
    fecha_meta: date
    plazo_dias: int
    composicion: ComposicionResponse
    viabilidad: ViabilidadResponse
    ingesta_kcal: float | None
    macros: MacrosResponse | None
    curva: CurvaResponse | None
    perdida: PerdidaResponse | None
    sensibilidad: SensibilidadResponse | None
    calculo: CalculoResponse | None
    equivalente_grasa: EquivalenteGrasaResponse | None = None


class PlanResponse(BaseModel):
    id: int
    fecha_inicio: date
    fecha_meta: date
    plazo_dias: int
    peso_inicial_kg: float
    peso_objetivo_kg: float
    ingesta_kcal: float
    proteina_g: float
    grasa_g: float
    carbohidratos_g: float
    composicion: ComposicionResponse
    tolerancia_kg: float
    estado: str
    creado_en: datetime
    dias_transcurridos: int
    dias_restantes: int
