"""Secante con salvaguarda: método de disparo (5.7)."""
from __future__ import annotations

from typing import Callable

from .constantes import MAX_ITER_SECANTE, TOL_SECANTE_KG
from .energia import tdee
from .modelo import simular_composicion
from .tipos import ErrorMotor, PasoSecante, Perfil, ResultadoSecante


def secante_salvaguardada(f: Callable[[float], float], a: float, b: float, tol: float = TOL_SECANTE_KG,
                          max_iter: int = MAX_ITER_SECANTE) -> ResultadoSecante:
    """Raíz de f en [a, b] con f(a) ≤ 0 < f(b).

    I0 = a, I1 = punto medio. Si el paso de la Secante sale del intervalo o
    f(I_k) = f(I_(k−1)), se usa bisección. El intervalo se actualiza en cada paso
    para que siga encerrando la raíz.
    """
    fa = f(a)
    hist = [PasoSecante(0, a, fa, "extremo a")]
    if abs(fa) < tol:
        return ResultadoSecante(a, fa, hist)
    fb = f(b)
    if fa > 0 or fb <= 0:
        raise ErrorMotor("sin_cambio_de_signo", "No hay una ingesta en el intervalo que llegue exactamente a la meta.")

    x0, f0 = a, fa
    x1 = (a + b) / 2.0
    f1 = f(x1)
    hist.append(PasoSecante(1, x1, f1, "punto medio"))
    if f1 > 0:
        b, fb = x1, f1
    else:
        a, fa = x1, f1
    if abs(f1) < tol:
        return ResultadoSecante(x1, f1, hist)

    for k in range(2, max_iter + 1):
        paso = "secante"
        if f1 != f0:
            x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
            if not a < x2 < b:
                x2, paso = (a + b) / 2.0, "bisección"
        else:
            x2, paso = (a + b) / 2.0, "bisección"
        f2 = f(x2)
        hist.append(PasoSecante(k, x2, f2, paso))
        if f2 > 0:
            b, fb = x2, f2
        else:
            a, fa = x2, f2
        if abs(f2) < tol:
            return ResultadoSecante(x2, f2, hist)
        x0, f0, x1, f1 = x1, f1, x2, f2

    raise ErrorMotor("secante_sin_convergencia",
                     f"No se encontró la ingesta en {max_iter} iteraciones. Intenta con otro plazo.")


def biseccion(f: Callable[[float], float], a: float, b: float, tol: float = TOL_SECANTE_KG,
              max_iter: int = 200) -> ResultadoSecante:
    """Bisección pura, solo para comparar en V2."""
    fa = f(a)
    hist = []
    for k in range(max_iter):
        m = (a + b) / 2.0
        fm = f(m)
        hist.append(PasoSecante(k, m, fm, "bisección"))
        if abs(fm) < tol:
            return ResultadoSecante(m, fm, hist)
        if (fm > 0) == (fa > 0):
            a, fa = m, fm
        else:
            b = m
    raise ErrorMotor("biseccion_sin_convergencia", "La bisección no convergió.")


def error_disparo(F0: float, L0: float, perfil: Perfil, N: int, W_meta: float) -> Callable[[float], float]:
    """f(I) = W_N(I) − W_meta. Cada evaluación es una simulación completa."""
    def f(I: float) -> float:
        return simular_composicion(F0, L0, perfil, I, N).peso_final() - W_meta
    return f


def calcular_ingesta_meta(F0: float, L0: float, perfil: Perfil, N: int, W_meta: float,
                          i_rapida: float) -> ResultadoSecante:
    """I* en [I_ráp, TDEE(W0)]."""
    return secante_salvaguardada(error_disparo(F0, L0, perfil, N, W_meta), i_rapida, tdee(F0 + L0, perfil))
