"""MacroSolver - logica principal (sin base de datos)."""

__version__ = "0.3.0-beta"

from .modelo import FACTORES_ACTIVIDAD, KCAL_POR_KG, Perfil, macros, tdee, tmb
from .metodos_numericos import (
    calcular_ingesta_meta,
    euler,
    regresion_exponencial,
    secante,
)
from .ciclo import advertencias, ejecutar_ciclo
from .datos_prueba import generar_datos_prueba, parsear_pares

__all__ = [
    "__version__", "FACTORES_ACTIVIDAD", "KCAL_POR_KG", "Perfil", "macros", "tdee", "tmb",
    "calcular_ingesta_meta", "euler", "regresion_exponencial", "secante",
    "advertencias", "ejecutar_ciclo", "generar_datos_prueba", "parsear_pares",
]
