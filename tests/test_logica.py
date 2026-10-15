"""
Verificaciones de la logica principal.

    python tests/test_logica.py        (sin instalar nada extra)
    python -m pytest tests             (si tienes pytest)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from macrosolver import (  # noqa: E402
    Perfil, calcular_ingesta_meta, ejecutar_ciclo, euler, generar_datos_prueba,
    parsear_pares, regresion_exponencial, tdee,
)

P = Perfil("M", 28, 175, 1.55)


def test_euler_en_equilibrio():
    """Si se come exactamente el TDEE, el peso no cambia."""
    w = euler(90, tdee(90, P), 30, P)
    assert abs(w[-1] - 90) < 1e-9


def test_secante_llega_a_la_meta():
    ing, _ = calcular_ingesta_meta(90, 82, 60, P)
    assert abs(euler(90, ing, 60, P)[-1] - 82) < 1e-4


def test_regresion_exponencial_recupera_parametros():
    xs = np.array([0, 7, 14, 21, 28])
    C, A = regresion_exponencial(xs, 80 * np.exp(-0.002 * xs))
    assert abs(C - 80) < 1e-9 and abs(A + 0.002) < 1e-12


def test_replanea_si_come_de_mas():
    ing, _ = calcular_ingesta_meta(90, 82, 60, P)
    kcal, pesos = generar_datos_prueba(ing, P, 90, 28, desvio_kcal=300, seed=1)
    res = ejecutar_ciclo(P, 90, 82, 60, kcal, pesos, 1.0)
    assert res["replanear"] and res["nuevo"]
    assert res["nuevo"]["ingesta"] < ing
    assert abs(res["nuevo"]["curva"][-1] - 82) < 1e-3


def test_no_replanea_con_adherencia_perfecta():
    ing, _ = calcular_ingesta_meta(90, 82, 60, P)
    kcal, pesos = generar_datos_prueba(ing, P, 90, 28, desvio_kcal=0, ruido_kcal=0, ruido_peso=0, seed=1)
    assert not ejecutar_ciclo(P, 90, 82, 60, kcal, pesos, 1.0)["replanear"]


def test_parsear_pares():
    pares, errs = parsear_pares("1, 2000\n2;1900.5\n# comentario\n\nabc\n3 1800")
    assert pares == [(1, 2000.0), (2, 1900.5), (3, 1800.0)] and len(errs) == 1


if __name__ == "__main__":
    pruebas = [f for n, f in sorted(globals().items()) if n.startswith("test_")]
    for f in pruebas:
        f()
        print(f"[ok] {f.__name__}")
    print(f"\nTodas las verificaciones pasaron ({len(pruebas)}).")
