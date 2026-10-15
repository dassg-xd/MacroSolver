"""Modelo fisiologico (seccion 3 del README): TMB, TDEE y macronutrientes."""
from __future__ import annotations

from dataclasses import dataclass

KCAL_POR_KG = 7700.0

FACTORES_ACTIVIDAD = {
    "Sedentario (1.2)": 1.2,
    "Ligera (1.375)": 1.375,
    "Moderada (1.55)": 1.55,
    "Alta (1.725)": 1.725,
    "Muy alta (1.9)": 1.9,
}


@dataclass
class Perfil:
    sexo: str            # "M" o "F"
    edad: float          # anios
    altura_cm: float
    factor_actividad: float


def tmb(peso_kg: float, p: Perfil) -> float:
    """Tasa Metabolica Basal (Mifflin-St Jeor)."""
    base = 10 * peso_kg + 6.25 * p.altura_cm - 5 * p.edad
    return base + 5 if p.sexo == "M" else base - 161


def tdee(peso_kg: float, p: Perfil) -> float:
    """Gasto Energetico Total Diario."""
    return tmb(peso_kg, p) * p.factor_actividad


def macros(calorias: float, peso_kg: float) -> dict:
    """Proteinas = 2*W, Grasas = 25% de las kcal, Carbohidratos = el resto."""
    proteina = 2.0 * peso_kg
    grasa = 0.25 * calorias / 9.0
    carbo = max(0.0, (calorias - proteina * 4 - grasa * 9) / 4.0)
    return {"proteina_g": proteina, "grasa_g": grasa, "carbohidratos_g": carbo}
