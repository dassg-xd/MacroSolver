"""Campos editables del perfil (HU-03)."""
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.auth import EDAD_MAXIMA, EDAD_MINIMA, calcular_edad

FACTORES_ACTIVIDAD_VALIDOS = {
    Decimal("1.2"),
    Decimal("1.375"),
    Decimal("1.55"),
    Decimal("1.725"),
    Decimal("1.9"),
}


class PerfilUpdateRequest(BaseModel):
    """Todos los campos son opcionales: PATCH solo cambia lo enviado."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    sexo: Literal["Masculino", "Femenino"] | None = None
    fecha_nacimiento: date | None = None
    altura_cm: Decimal | None = Field(default=None, ge=100, le=250)
    factor_actividad: Decimal | None = None
    nivel_entrenamiento: Literal[
        "principiante", "intermedio", "avanzado"
    ] | None = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        nombre = valor.strip()
        if not nombre:
            raise ValueError("El nombre no puede estar vacío.")
        return nombre

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha_nacimiento(cls, valor: date | None) -> date | None:
        if valor is None:
            return None
        hoy = date.today()
        if valor >= hoy:
            raise ValueError("La fecha de nacimiento debe ser anterior a hoy.")
        edad = calcular_edad(valor, hoy)
        if edad < EDAD_MINIMA:
            raise ValueError(
                f"Debes tener al menos {EDAD_MINIMA} años para usar MacroSolver."
            )
        if edad > EDAD_MAXIMA:
            raise ValueError("Revisa la fecha de nacimiento.")
        return valor

    @field_validator("factor_actividad")
    @classmethod
    def validar_factor_actividad(cls, valor: Decimal | None) -> Decimal | None:
        if valor is None:
            return None
        if valor not in FACTORES_ACTIVIDAD_VALIDOS:
            raise ValueError("El factor de actividad no es válido.")
        return valor
