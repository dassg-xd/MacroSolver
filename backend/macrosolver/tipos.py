"""Tipos de datos y errores del motor."""
from __future__ import annotations

from dataclasses import dataclass, field

from .constantes import FACTORES_ACTIVIDAD


class ErrorMotor(ValueError):
    """Error de dominio del motor. El backend lo traduce a HTTP 422.

    `codigo` es estable para el frontend; `mensaje` va en español para el usuario.
    """

    def __init__(self, codigo: str, mensaje: str):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


@dataclass(frozen=True)
class Perfil:
    """Copia del perfil que se guarda en el plan (no cambia mientras el plan está activo)."""

    sexo: str            # "hombre" | "mujer"
    edad: int            # años cumplidos al crear el plan
    altura_cm: float
    f_act: float         # 1,2 · 1,375 · 1,55 · 1,725 · 1,9

    def __post_init__(self):
        if self.sexo not in ("hombre", "mujer"):
            raise ErrorMotor("sexo_invalido", "El sexo debe ser «hombre» o «mujer».")
        if not 18 <= self.edad <= 100:
            raise ErrorMotor("edad_invalida", "MacroSolver es para adultos: la edad debe estar entre 18 y 100 años.")
        if not 100 <= self.altura_cm <= 250:
            raise ErrorMotor("altura_invalida", "La altura debe estar entre 100 y 250 cm.")
        if not any(abs(self.f_act - f) < 1e-9 for f in FACTORES_ACTIVIDAD):
            raise ErrorMotor("factor_invalido", "El factor de actividad no es uno de los valores permitidos.")

    @property
    def s(self) -> float:
        """Término de sexo de Mifflin-St Jeor."""
        return 5.0 if self.sexo == "hombre" else -161.0

    def con_f_act(self, f_act: float) -> "Perfil":
        """Copia con otro factor de actividad, sin validar (la usa la sensibilidad)."""
        p = object.__new__(Perfil)
        object.__setattr__(p, "sexo", self.sexo)
        object.__setattr__(p, "edad", self.edad)
        object.__setattr__(p, "altura_cm", self.altura_cm)
        object.__setattr__(p, "f_act", f_act)
        return p


@dataclass
class Trayectoria:
    """Resultado de una simulación. Índice i = día i (convención de la sección 4)."""

    t: list[float]
    W: list[float]
    F: list[float]
    L: list[float]
    B: list[float]                     # balance usado en cada paso (len = pasos)
    estimado: list[bool] = field(default_factory=list)   # por día, solo en adherencia

    def peso_final(self) -> float:
        return self.W[-1]


@dataclass
class PasoSecante:
    k: int
    ingesta: float
    f: float
    paso: str            # "extremo a" | "punto medio" | "secante" | "bisección"


@dataclass
class ResultadoSecante:
    raiz: float
    f_raiz: float
    historial: list[PasoSecante]

    @property
    def iteraciones(self) -> int:
        return len(self.historial)
