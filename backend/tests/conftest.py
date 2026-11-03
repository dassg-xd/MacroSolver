import os

# Valores de prueba para que la app se importe sin un .env real (no se conecta a Supabase).
os.environ.setdefault("SUPABASE_URL", "https://prueba.supabase.co")
os.environ.setdefault("SUPABASE_SECRET_KEY", "sb_secret_prueba")
os.environ.setdefault("JWT_SECRET", "secreto-de-prueba-con-mas-de-32-caracteres")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import pytest

from macrosolver import Perfil, estimar_grasa


@pytest.fixture
def hombre():
    return Perfil("hombre", 23, 176, 1.375)


@pytest.fixture
def mujer():
    return Perfil("mujer", 30, 162, 1.55)


@pytest.fixture
def comp_hombre(hombre):
    """82 kg, cuello 39, cintura 101 → ≈ 27 % de grasa."""
    return estimar_grasa(hombre, 82.0, cuello=39, cintura=101)
