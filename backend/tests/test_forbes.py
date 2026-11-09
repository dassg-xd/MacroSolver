"""Relación grasa ↔ peso de Forbes: forma cerrada, inversa y concordancia con Euler."""
import math

import pytest

from macrosolver import (ErrorMotor, grasa_para_peso, masa_libre_para_grasa, meta_por_grasa,
                         peso_para_grasa, simular_composicion)


def test_forma_cerrada_en_el_punto_inicial():
    assert masa_libre_para_grasa(13.3, 56.7, 13.3) == pytest.approx(56.7)
    assert peso_para_grasa(13.3, 56.7, 13.3) == pytest.approx(70.0)


def test_caso_de_la_pantalla():
    """Perder 2,2 kg de grasa con 13,3 kg iniciales arrastra ≈ 1,9 kg de masa libre."""
    perdida_libre = 56.7 - masa_libre_para_grasa(13.3, 56.7, 13.3 - 2.2)
    assert perdida_libre == pytest.approx(10.4 * math.log(13.3 / 11.1), abs=1e-9)
    assert 1.8 < perdida_libre < 1.95


def test_inversa():
    F0, L0 = 20.0, 62.0
    for W in (81.9, 78.0, 72.5, 65.0):
        F = grasa_para_peso(F0, L0, W)
        assert peso_para_grasa(F0, L0, F) == pytest.approx(W, abs=1e-6)


def test_euler_sigue_la_curva_de_forbes(hombre, comp_hombre):
    """El reparto no depende de la ingesta: con cualquier I la trayectoria cae sobre W(F)."""
    F0, L0 = comp_hombre.F0, comp_hombre.L0
    for ingesta in (1500.0, 1900.0, 2300.0):
        tr = simular_composicion(F0, L0, hombre, ingesta, 120)
        for F, L in zip(tr.F[::20], tr.L[::20]):
            assert L == pytest.approx(masa_libre_para_grasa(F0, L0, F), abs=0.03)


def test_meta_por_grasa():
    m = meta_por_grasa(13.3, 56.7, "hombre", 4.0)
    assert m.grasa_final_kg == pytest.approx(9.3)
    assert m.peso_meta_kg == pytest.approx(9.3 + 56.7 + 10.4 * math.log(9.3 / 13.3))
    assert 70.0 - m.peso_meta_kg > 7.0          # 4 kg de grasa ≈ 7,7 kg de peso
    assert m.segura


def test_meta_por_grasa_bajo_el_minimo():
    m = meta_por_grasa(13.3, 56.7, "hombre", 10.0)
    assert not m.segura


@pytest.mark.parametrize("perder", [0.0, -1.0, 13.3, 20.0])
def test_meta_por_grasa_invalida(perder):
    with pytest.raises(ErrorMotor):
        meta_por_grasa(13.3, 56.7, "hombre", perder)
