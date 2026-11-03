"""Validación numérica V1–V8 (sección 8 del documento v0.5)."""
import math
import random

import pytest

from macrosolver import (biseccion, calcular_ingesta_meta, calcular_tendencia, cumple_bloqueos,
                         derivada_central, derivada_progresiva, equilibrio, error_disparo,
                         estimar_grasa, euler_simple, evaluar_viabilidad, recurrencia_exacta_lineal,
                         referencia_rk4, regresion_exponencial, secante_salvaguardada,
                         simular_adherencia, simular_composicion, solucion_exacta_lineal, tdee)
from macrosolver.constantes import RHO_F, RHO_L, RHO_SIMPLE
from macrosolver.tipos import Perfil
from macrosolver.viabilidad import ingesta_rapida

N = 90
I_PRUEBA = 1900.0


def orden_observado(e_h, e_h2):
    return math.log(e_h / e_h2) / math.log(2)


# ---------------------------------------------------------------- V1
class TestV1OrdenEuler:
    def test_lineal_frente_a_solucion_exacta(self, hombre):
        exacta = solucion_exacta_lineal(82.0, hombre, I_PRUEBA, N)
        errores = [abs(euler_simple(82.0, hombre, I_PRUEBA, N, h=h)[-1] - exacta) for h in (1.0, 0.5, 0.25)]
        for e1, e2 in zip(errores, errores[1:]):
            assert 0.9 <= orden_observado(e1, e2) <= 1.1

    def test_no_lineal_frente_a_rk4(self, hombre, comp_hombre):
        F0, L0 = comp_hombre.F0, comp_hombre.L0
        ref = referencia_rk4(F0, L0, hombre, I_PRUEBA, N, h=0.05).W[-1]
        errores = [abs(simular_composicion(F0, L0, hombre, I_PRUEBA, N, h=h).W[-1] - ref) for h in (1.0, 0.5, 0.25)]
        for e1, e2 in zip(errores, errores[1:]):
            assert 0.9 <= orden_observado(e1, e2) <= 1.1

    def test_error_despreciable_con_h_1(self, hombre, comp_hombre):
        """El error de discretización con h = 1 día es mucho menor que 0,01 kg."""
        F0, L0 = comp_hombre.F0, comp_hombre.L0
        ref = referencia_rk4(F0, L0, hombre, I_PRUEBA, N).W[-1]
        assert abs(simular_composicion(F0, L0, hombre, I_PRUEBA, N).W[-1] - ref) < 0.01


# ---------------------------------------------------------------- V2
class TestV2Secante:
    def test_menos_iteraciones_que_biseccion(self, hombre, comp_hombre):
        F0, L0 = comp_hombre.F0, comp_hombre.L0
        v = evaluar_viabilidad(F0, L0, hombre, 75.0, N)
        f = error_disparo(F0, L0, hombre, N, 75.0)
        a, b = v.i_rapida, tdee(82.0, hombre)
        sec = secante_salvaguardada(f, a, b)
        bis = biseccion(f, a, b)
        assert abs(sec.f_raiz) < 0.01
        assert sec.iteraciones < bis.iteraciones

    def test_f_creciente(self, hombre, comp_hombre):
        f = error_disparo(comp_hombre.F0, comp_hombre.L0, hombre, N, 75.0)
        malla = [1500 + 25 * k for k in range(41)]
        valores = [f(I) for I in malla]
        assert all(v2 > v1 for v1, v2 in zip(valores, valores[1:]))

    def test_caso_lineal_converge_en_una_iteracion(self, hombre):
        """En euler_simple f es afín: el primer paso de Secante cae en la raíz."""
        W_meta = 75.0

        def f(I):
            return euler_simple(82.0, hombre, I, N)[-1] - W_meta

        res = secante_salvaguardada(f, 1700.0, tdee(82.0, hombre))
        pasos_secante = [p for p in res.historial if p.paso == "secante"]
        assert len(pasos_secante) == 1
        assert abs(res.f_raiz) < 1e-6


# ---------------------------------------------------------------- V3
class TestV3Regresion:
    def test_sin_ruido_recupera_parametros(self):
        C, A = 82.0, -0.0012
        xs = list(range(0, 40, 3))
        ys = [C * math.exp(A * x) for x in xs]
        t = regresion_exponencial([float(x) for x in xs], ys)
        assert abs(t.C - C) < 1e-9
        assert abs(t.A - A) < 1e-9
        assert t.r2 == pytest.approx(1.0)

    def test_con_ruido_documenta_error(self):
        rnd = random.Random(7)
        C, A = 82.0, -0.0012
        xs = list(range(0, 60, 2))
        ys = [C * math.exp(A * x) + rnd.gauss(0, 0.3) for x in xs]
        t = regresion_exponencial([float(x) for x in xs], ys)
        # Con ruido de 0,3 kg el error relativo de A queda por debajo del 15 %.
        assert abs(t.A - A) / abs(A) < 0.15


# ---------------------------------------------------------------- V4
def test_v4_conservacion_de_energia(hombre, comp_hombre):
    tr = simular_composicion(comp_hombre.F0, comp_hombre.L0, hombre, I_PRUEBA, N)
    dF = tr.F[-1] - tr.F[0]
    dL = tr.L[-1] - tr.L[0]
    suma_B = sum(tr.B)
    eps = abs(RHO_F * dF + RHO_L * dL - suma_B) / abs(suma_B)
    assert eps < 1e-10


# ---------------------------------------------------------------- euler_simple (ver V5 en test_v5_beta.py)
class TestEulerSimple:
    """euler_simple (modelo lineal). Las 6 pruebas originales de la beta están en test_v5_beta.py."""

    def test_igual_al_euler_de_la_beta(self):
        from macrosolver import beta
        pb = beta.Perfil("M", 28, 175, 1.55)
        pn = Perfil("hombre", 28, 175, 1.55)
        assert euler_simple(90.0, pn, 2100.0, 60) == pytest.approx(beta.euler(90.0, 2100.0, 60, pb), abs=1e-12)

    def test_longitud(self, hombre):
        assert len(euler_simple(82.0, hombre, I_PRUEBA, N)) == N + 1

    def test_equilibrio_estable(self, hombre):
        W = euler_simple(80.0, hombre, tdee(80.0, hombre), 30)
        assert max(abs(w - 80.0) for w in W) < 1e-9

    def test_deficit_baja_peso(self, hombre):
        W = euler_simple(82.0, hombre, 1800.0, 30)
        assert all(b < a for a, b in zip(W, W[1:]))

    def test_superavit_sube_peso(self, hombre):
        W = euler_simple(70.0, hombre, 3200.0, 30)
        assert all(b > a for a, b in zip(W, W[1:]))

    def test_recurrencia_cerrada(self, hombre):
        W = euler_simple(82.0, hombre, I_PRUEBA, N)
        for i in (0, 1, 10, 45, 90):
            assert W[i] == pytest.approx(recurrencia_exacta_lineal(82.0, hombre, I_PRUEBA, i), abs=1e-9)

    def test_tiende_al_equilibrio(self, hombre):
        Wst = equilibrio(I_PRUEBA, hombre)
        W = euler_simple(82.0, hombre, I_PRUEBA, 8000)   # constante de tiempo ≈ 560 días
        assert abs(W[-1] - Wst) < 0.05


# ---------------------------------------------------------------- V6
def test_v6_sensibilidad_central_vs_progresiva(hombre, comp_hombre):
    F0, L0 = comp_hombre.F0, comp_hombre.L0

    def g(f_act):
        return simular_composicion(F0, L0, hombre.con_f_act(f_act), I_PRUEBA, N).W[-1]

    theta = hombre.f_act
    ref = derivada_central(g, theta, 1e-4)
    pasos = [0.1, 0.05, 0.025]
    e_c = [abs(derivada_central(g, theta, d) - ref) for d in pasos]
    e_p = [abs(derivada_progresiva(g, theta, d) - ref) for d in pasos]
    for a, b in zip(e_c, e_c[1:]):
        assert 3.5 < a / b < 4.5      # O(Δ²)
    for a, b in zip(e_p, e_p[1:]):
        assert 1.8 < a / b < 2.2      # O(Δ)


# ---------------------------------------------------------------- V7
def test_v7_convencion_de_indices(hombre, comp_hombre):
    """Un registro de calorías en el día d afecta a W desde d + 1."""
    F0, L0 = comp_hombre.F0, comp_hombre.L0
    d = 12
    base = simular_adherencia(F0, L0, hombre, I_PRUEBA, 30, {}).W
    con = simular_adherencia(F0, L0, hombre, I_PRUEBA, 30, {d: 2600.0}).W
    assert con[: d + 1] == base[: d + 1]
    assert con[d + 1] > base[d + 1]


# ---------------------------------------------------------------- V8
CASOS_V8 = [
    (Perfil("hombre", 23, 176, 1.375), 82.0, 39, 101, None, 75.0),
    (Perfil("hombre", 45, 170, 1.2), 95.0, 42, 108, None, 85.0),
    (Perfil("hombre", 30, 185, 1.725), 100.0, 41, 100, None, 90.0),
    (Perfil("mujer", 30, 162, 1.55), 70.0, 33, 82, 102, 63.0),
    (Perfil("mujer", 55, 158, 1.2), 78.0, 35, 92, 108, 72.0),
    (Perfil("mujer", 19, 168, 1.9), 64.0, 31, 72, 96, 60.0),
]


@pytest.mark.parametrize("perfil,W0,cuello,cintura,cadera,W_meta", CASOS_V8)
def test_v8_plazo_minimo_cumple_bloqueos(perfil, W0, cuello, cintura, cadera, W_meta):
    comp = estimar_grasa(perfil, W0, cuello, cintura, cadera)
    v = evaluar_viabilidad(comp.F0, comp.L0, perfil, W_meta, 10_000)
    assert v.alcanzable
    N_min = v.n_min_dias
    assert evaluar_viabilidad(comp.F0, comp.L0, perfil, W_meta, N_min).viable
    assert not evaluar_viabilidad(comp.F0, comp.L0, perfil, W_meta, N_min - 1).viable
    res = calcular_ingesta_meta(comp.F0, comp.L0, perfil, N_min, W_meta, v.i_rapida)
    assert abs(res.f_raiz) < 0.01
    assert cumple_bloqueos(res.raiz, W0, perfil)
    assert res.raiz >= ingesta_rapida(W0, perfil) - 1e-9
