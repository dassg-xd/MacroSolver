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
