"""Reglas de negocio del motor: dominios, respaldos, re-planeación, estadísticas y rendimiento."""
import time
from datetime import date

import pytest

from macrosolver import (ErrorMotor, Perfil, calcular_seguimiento, calcular_vista_previa,
                         composicion_replaneacion, estadisticas_semanales, estimar_grasa,
                         evaluar_replaneacion, macros, simular_composicion, tdee)
from macrosolver.energia import coeficientes_tdee


# ---------------------------------------------------------------- perfil y energía
def test_perfil_valida_factor():
    with pytest.raises(ErrorMotor) as e:
        Perfil("hombre", 25, 175, 1.4)
    assert e.value.codigo == "factor_invalido"


def test_tdee_es_afin(hombre):
    a, b = coeficientes_tdee(hombre)
    for W in (60.0, 80.0, 120.0):
        assert tdee(W, hombre) == pytest.approx(a * W + b)


# ---------------------------------------------------------------- composición
def test_marina_dominio_invalido(hombre):
    with pytest.raises(ErrorMotor) as e:
        estimar_grasa(hombre, 80.0, cuello=50, cintura=45)
    assert e.value.codigo == "medidas_invalidas"


def test_grasa_fuera_de_rango(hombre):
    with pytest.raises(ErrorMotor) as e:
        estimar_grasa(hombre, 80.0, cuello=40, cintura=60)
    assert e.value.codigo == "grasa_fuera_de_rango"


def test_respaldo_deurenberg_sin_cadera(mujer):
    c = estimar_grasa(mujer, 70.0, cuello=33, cintura=82)
    assert c.metodo == "deurenberg"
    assert c.F0 + c.L0 == pytest.approx(70.0)


# ---------------------------------------------------------------- macros
def test_macros_base():
    m = macros(2000.0, 60.0)
    assert m.proteina_g == pytest.approx(132.0)
    assert m.fraccion_grasa == 0.25
    assert 4 * m.proteina_g + 9 * m.grasa_g + 4 * m.carbohidratos_g == pytest.approx(2000.0)


def test_macros_baja_grasa_al_20():
    m = macros(1500.0, 130.0)     # 4·286 = 1144 kcal de proteína: con 25 % de grasa no alcanza
    assert m.fraccion_grasa == 0.20
    assert m.carbohidratos_g == pytest.approx(14.0)
    assert m.advertencia


def test_macros_imposibles():
    with pytest.raises(ErrorMotor):
        macros(900.0, 90.0)


# ---------------------------------------------------------------- vista previa
def test_vista_previa_viable(hombre):
    vp = calcular_vista_previa(hombre, 82.0, 75.0, 90, cuello=39, cintura=101)
    assert vp.viabilidad.viable
    assert len(vp.curva_ideal["W"]) == 91
    assert vp.curva_ideal["W"][-1] == pytest.approx(75.0, abs=0.01)
    assert vp.rango.minimo <= vp.ingesta <= vp.rango.maximo
    assert vp.historial_secante[0].paso == "extremo a"


def test_vista_previa_plazo_corto(hombre):
    vp = calcular_vista_previa(hombre, 82.0, 75.0, 40, cuello=39, cintura=101)
    assert not vp.viabilidad.viable
    assert vp.viabilidad.n_min_dias > 40
    assert vp.ingesta is None


def test_meta_inalcanzable():
    p = Perfil("mujer", 60, 150, 1.2)
    vp = calcular_vista_previa(p, 60.0, 40.0, 365)
    assert not vp.viabilidad.alcanzable


def test_meta_debe_ser_perdida(hombre):
    with pytest.raises(ErrorMotor):
        calcular_vista_previa(hombre, 80.0, 85.0, 90, cuello=39, cintura=95)


# ---------------------------------------------------------------- seguimiento y re-planeación
def _plan(hombre):
    vp = calcular_vista_previa(hombre, 82.0, 75.0, 90, cuello=39, cintura=101, con_sensibilidad=False)
    return vp.composicion.F0, vp.composicion.L0, vp.ingesta


def test_sugiere_replaneacion_cuando_va_por_encima(hombre):
    F0, L0, I = _plan(hombre)
    calorias = {i: I + 450 for i in range(24)}            # come de más
    real = simular_composicion(F0, L0, hombre, lambda i: calorias.get(i, I), 24).W
    pesos = {i: real[i] + 0.3 for i in (0, 3, 6, 10, 13, 17, 20, 24)}
    pesos[0] = 82.0
    s = calcular_seguimiento(hombre, F0, L0, I, 90, 75.0, 24, calorias, pesos)
    assert s.desviacion.sugerir
    assert s.desviacion.delta > 1.0
    assert s.llegada.retraso > 0


def test_no_sugiere_antes_del_dia_10(hombre):
    F0, L0, I = _plan(hombre)
    ideal = simular_composicion(F0, L0, hombre, I, 90).W
    pesos = {0: 82.0, 3: 83.0, 6: 83.5, 9: 84.0}
    d = evaluar_replaneacion(pesos, ideal, ideal, 75.0, 90, 9, set(pesos))
    assert not d.sugerir and "día 10" in d.motivo


def test_no_sugiere_con_mas_de_7_dias_sin_registro(hombre):
    F0, L0, I = _plan(hombre)
    ideal = simular_composicion(F0, L0, hombre, I, 90).W
    pesos = {0: 82.0, 5: 83.0, 10: 83.5, 14: 84.0}
    d = evaluar_replaneacion(pesos, ideal, ideal, 75.0, 90, 25, set(pesos))
    assert not d.sugerir and "7 días" in d.motivo


def test_composicion_replaneacion_conserva_masa_libre(hombre):
    c = composicion_replaneacion(W_real=80.6, L_sim=59.1, N=90, x_u=24, perfil=hombre)
    assert c.L0 == pytest.approx(59.1)
    assert c.F0 == pytest.approx(21.5)
    assert c.N == 66


def test_composicion_replaneacion_respaldo(hombre):
    c = composicion_replaneacion(W_real=62.0, L_sim=60.0, N=90, x_u=24, perfil=hombre)
    assert c.aviso is not None
    assert c.F0 > 0.05 * 62.0


def test_curva_con_ejercicio_baja_mas(hombre):
    F0, L0, I = _plan(hombre)
    calorias = {i: I for i in range(10)}
    act = {2: [(8.0, 30)], 4: [(5.0, 45)], 6: [(8.0, 30)]}
    s = calcular_seguimiento(hombre, F0, L0, I, 90, 75.0, 10, calorias, {0: 82.0}, actividades=act)
    assert s.curva_ejercicio is not None
    assert s.curva_ejercicio[7] != s.curva_adherencia[7]


# ---------------------------------------------------------------- estadísticas
def test_semanas_de_domingo_a_sabado():
    inicio = date(2026, 10, 27)        # martes
    cal = {0: 1960, 1: 2300, 2: 1900, 5: 1950, 6: 2000}
    pes = {0: 82.0, 3: 81.6, 6: 81.4, 10: 81.0}
    sem = estadisticas_semanales(inicio, 12, 1960.0, cal, pes, {2: [(8.0, 30)]})
    assert sem[0].inicio == date(2026, 10, 25)          # domingo
    assert sem[0].dias_registrados == 3                  # días 0, 1 y 2 (27 a 29 oct)
    assert sem[0].dias_cumplidos == 2                    # 2300 se sale del ±10 %
    assert sem[1].variacion == pytest.approx(81.2 - sem[0].peso_promedio)
    assert sem[-1].parcial and not sem[1].parcial
    assert sem[0].sesiones == 1


# ---------------------------------------------------------------- rendimiento (sección 9)
def test_vista_previa_rapida_en_plan_largo():
    p = Perfil("hombre", 35, 180, 1.55)
    t0 = time.perf_counter()
    vp = calcular_vista_previa(p, 120.0, 100.0, 365, cuello=44, cintura=120)
    assert vp.viabilidad.viable
    assert time.perf_counter() - t0 < 2.0
