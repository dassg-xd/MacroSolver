from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Mismos límites que la base de datos (plan.edad_anios entre 18 y 100) y el README.
EDAD_MINIMA = 18
EDAD_MAXIMA = 100
CONTRASENA_MINIMA = 8


def calcular_edad(fecha_nacimiento: date, hoy: date | None = None) -> int:
    """Años cumplidos a la fecha 'hoy'."""
    hoy = hoy or date.today()
    cumplio = (hoy.month, hoy.day) >= (fecha_nacimiento.month, fecha_nacimiento.day)
    return hoy.year - fecha_nacimiento.year - (0 if cumplio else 1)


class RegistroRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    correo: EmailStr
    contrasena: str
    nombre: str = Field(min_length=1, max_length=150)
    sexo: Literal["Masculino", "Femenino"]
    fecha_nacimiento: date
    altura_cm: Decimal = Field(ge=100, le=250)
    factor_actividad: Decimal
    nivel_entrenamiento: Literal[
        "principiante", "intermedio", "avanzado"
    ] = "principiante"

    @field_validator("contrasena")
    @classmethod
    def validar_contrasena(cls, valor: str) -> str:
        if len(valor) < CONTRASENA_MINIMA:
            raise ValueError(
                f"La contraseña debe tener al menos {CONTRASENA_MINIMA} caracteres."
            )
        if not valor.strip():
            raise ValueError("La contraseña no puede ser solo espacios.")
        if len(valor.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes en UTF-8.")
        return valor

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, valor: str) -> str:
        nombre = valor.strip()
        if not nombre:
            raise ValueError("El nombre no puede estar vacío.")
        return nombre

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha_nacimiento(cls, valor: date) -> date:
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
    def validar_factor_actividad(cls, valor: Decimal) -> Decimal:
        factores_validos = {
            Decimal("1.2"),
            Decimal("1.375"),
            Decimal("1.55"),
            Decimal("1.725"),
            Decimal("1.9"),
        }
        if valor not in factores_validos:
            raise ValueError("El factor de actividad no es válido.")
        return valor


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    correo: EmailStr
    contrasena: str = Field(min_length=1)


class UsuarioPublico(BaseModel):
    id: int
    correo: EmailStr
    nombre: str
    sexo: Literal["Masculino", "Femenino"]
    fecha_nacimiento: date
    altura_cm: Decimal
    factor_actividad: Decimal
    nivel_entrenamiento: Literal[
        "principiante", "intermedio", "avanzado"
    ]
    creado_en: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    usuario: UsuarioPublico