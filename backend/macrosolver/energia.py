"""Gasto energético (5.2): fórmulas cerradas."""
from .tipos import Perfil


def imc(peso: float, altura_cm: float) -> float:
    return peso / (altura_cm / 100.0) ** 2


def tmb(peso: float, perfil: Perfil) -> float:
    """Tasa metabólica basal de Mifflin-St Jeor, kcal/día."""
    return 10.0 * peso + 6.25 * perfil.altura_cm - 5.0 * perfil.edad + perfil.s


def tdee(peso: float, perfil: Perfil) -> float:
    """Gasto total diario: f_act · TMB(W)."""
    return perfil.f_act * tmb(peso, perfil)


def coeficientes_tdee(perfil: Perfil) -> tuple[float, float]:
    """TDEE(W) = a·W + b. Devuelve (a, b)."""
    a = 10.0 * perfil.f_act
    b = perfil.f_act * (6.25 * perfil.altura_cm - 5.0 * perfil.edad + perfil.s)
    return a, b


def equilibrio(ingesta: float, perfil: Perfil) -> float:
    """Peso W* donde TDEE(W*) = I. Con esa ingesta el peso tiende a W*."""
    return (ingesta / perfil.f_act - (6.25 * perfil.altura_cm - 5.0 * perfil.edad + perfil.s)) / 10.0
