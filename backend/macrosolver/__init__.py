"""MacroSolver: motor numérico puro (sin base de datos ni red).

Euler sobre un modelo de dos compartimentos, Secante como método de disparo,
mínimos cuadrados para la tendencia y diferencias finitas para la sensibilidad.
Ecuaciones: sección 5 del Documento de software v0.5.
"""
from .ciclo import Seguimiento, VistaPrevia, calcular_seguimiento, calcular_vista_previa, ejecutar_ciclo
from .composicion import Composicion, composicion_desde_pct, estimar_grasa, grasa_deurenberg, grasa_marina
from .energia import coeficientes_tdee, equilibrio, imc, tdee, tmb
from .estadisticas import Semana, estadisticas_semanales, gasto_ejercicio_dia
from .macros import Macros, macros
from .modelo import (euler_simple, fraccion_libre, recurrencia_exacta_lineal, referencia_rk4,
                     simular_composicion, solucion_exacta_lineal)
from .secante import biseccion, calcular_ingesta_meta, error_disparo, secante_salvaguardada
from .seguimiento import (calcular_tendencia, composicion_replaneacion, evaluar_replaneacion,
                          llegada_estimada, regresion_exponencial, simular_adherencia)
from .sensibilidad import derivada_central, derivada_progresiva, rango_ingesta
from .tipos import ErrorMotor, Perfil, Trayectoria
from .viabilidad import cumple_bloqueos, evaluar_viabilidad, ingesta_minima, ingesta_rapida

__version__ = "0.1.0"
