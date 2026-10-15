"""
Demo SIN interfaz web (solo necesita numpy y matplotlib).
Imprime el resumen en consola y guarda las graficas en la carpeta salida/.

    python ejecutar_demo.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from macrosolver import Perfil, calcular_ingesta_meta, ejecutar_ciclo, generar_datos_prueba  # noqa: E402
from macrosolver.ciclo import resumen  # noqa: E402
from macrosolver.graficas import graficar_calorias, graficar_pesos  # noqa: E402

SALIDA = Path(__file__).parent / "salida"
SALIDA.mkdir(exist_ok=True)

p = Perfil(sexo="M", edad=28, altura_cm=175, factor_actividad=1.55)
w0, w_obj, dias = 90.0, 82.0, 60

ingesta, _ = calcular_ingesta_meta(w0, w_obj, dias, p)
kcal, pesos = generar_datos_prueba(ingesta, p, w0, dias_sim=28, desvio_kcal=300)
res = ejecutar_ciclo(p, w0, w_obj, dias, kcal, pesos, tolerancia_kg=1.0)

print(resumen(res))
graficar_pesos(res).savefig(SALIDA / "grafica_pesos.png", dpi=130)
graficar_calorias(res).savefig(SALIDA / "grafica_calorias.png", dpi=130)
print(f"\nGraficas guardadas en: {SALIDA}")
