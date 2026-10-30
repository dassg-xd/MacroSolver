from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class RegistroRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    correo: EmailStr
    contrasena: str = Field(min_length=8)
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
    def validar_longitud_bcrypt(cls, valor: str) -> str:
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
        if valor >= date.today():
            raise ValueError("La fecha de nacimiento debe ser anterior a hoy.")
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
    contrasena: str


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