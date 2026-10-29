"""Constantes del modelo (sección 5.1 del documento v0.5)."""

RHO_F = 9400.0          # densidad energética de la grasa, kcal/kg
RHO_L = 1800.0          # densidad energética de la masa libre de grasa, kcal/kg
RHO_SIMPLE = 7700.0     # densidad única del modelo lineal (euler_simple)
C_F = 10.4 * RHO_L / RHO_F   # constante de Forbes ≈ 1,99 kg

DEFICIT_MAXIMO = 700.0  # kcal/día, regla del proyecto (5.6)
INGESTA_MINIMA = {"hombre": 1500.0, "mujer": 1200.0}

FACTORES_ACTIVIDAD = (1.2, 1.375, 1.55, 1.725, 1.9)
FACTOR_BASE_EJERCICIO = 1.2   # días con actividad registrada (5.12)

PCT_GRASA_MIN, PCT_GRASA_MAX = 5.0, 60.0

TOL_SECANTE_KG = 0.01
MAX_ITER_SECANTE = 30
HORIZONTE_LLEGADA = 180       # días (5.9)
TOLERANCIA_REPLANEACION = 1.0  # kg
DIA_MINIMO_REPLANEACION = 10
PESOS_MINIMOS_REPLANEACION = 3
MAX_DIAS_SIN_REGISTRO = 7

PROTEINA_G_POR_KG_LIBRE = 2.2
KCAL_G_PROTEINA = KCAL_G_CHO = 4.0
KCAL_G_GRASA = 9.0
FRACCION_GRASA = 0.25
FRACCION_GRASA_RESPALDO = 0.20

ADHERENCIA_BANDA = 0.10       # ±10 % de I*

# MET iniciales (a confirmar en el Compendio de Actividades Físicas)
MET = {"Caminata": 3.5, "Trote": 8.0, "Ciclismo": 8.0, "Natación": 6.0, "Pesas": 5.0}
