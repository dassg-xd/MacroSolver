"""
MacroSolver - interfaz de prueba (Streamlit). NO usa base de datos.

Ejecutar (desde esta carpeta):
    python -m streamlit run app.py
o simplemente:
    python app.py        (abre la interfaz en el navegador)
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys

from macrosolver import (
    FACTORES_ACTIVIDAD, Perfil, __version__, advertencias, calcular_ingesta_meta,
    ejecutar_ciclo, generar_datos_prueba, parsear_pares,
)


def interfaz():
    import matplotlib.pyplot as plt
    import streamlit as st
    from macrosolver.graficas import graficar_calorias, graficar_pesos

    st.set_page_config(page_title="MacroSolver beta", layout="wide")
    st.title("MacroSolver (beta)")
    st.caption(f"Version {__version__} · Datos de prueba, sin base de datos · "
               "Euler + Secante + Minimos Cuadrados + Re-planeacion")

    # ---- Barra lateral: perfil y plan --------------------------------------
    with st.sidebar:
        st.header("Perfil")
        sexo = st.radio("Sexo", ["M", "F"], horizontal=True)
        edad = st.number_input("Edad (anios)", 14, 90, 28)
        altura = st.number_input("Altura (cm)", 120.0, 230.0, 175.0, step=1.0)
        factor_txt = st.selectbox("Actividad", list(FACTORES_ACTIVIDAD), index=2)
        st.header("Plan")
        w0 = st.number_input("Peso inicial (kg)", 30.0, 250.0, 90.0, step=0.5)
        w_obj = st.number_input("Peso objetivo (kg)", 30.0, 250.0, 82.0, step=0.5)
        dias = st.number_input("Plazo (dias)", 7, 365, 60)
        tol = st.number_input("Tolerancia para re-planear (kg)", 0.1, 10.0, 1.0, step=0.1)

    p = Perfil(sexo, float(edad), float(altura), FACTORES_ACTIVIDAD[factor_txt])

    try:
        ingesta_plan, _ = calcular_ingesta_meta(float(w0), float(w_obj), int(dias), p)
    except Exception as e:  # noqa: BLE001
        st.error(f"No se pudo calcular el plan: {e}")
        return

    # ---- Datos de prueba ---------------------------------------------------
    with st.expander("Generador de datos de prueba", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        dias_sim = c1.number_input("Dias a simular", 2, int(dias), min(28, int(dias)))
        desvio = c2.slider("Desvio medio de kcal vs plan", -600, 900, 300, step=50,
                           help="Positivo = come de mas (se estanca). Negativo = come de menos.")
        r_kcal = c3.slider("Variabilidad diaria (kcal)", 0, 600, 250, step=50)
        r_peso = c4.slider("Ruido de la bascula (kg)", 0.0, 1.0, 0.25, step=0.05)
        if st.button("Generar datos de prueba", type="primary") or "txt_kcal" not in st.session_state:
            kcal, pesos_gen = generar_datos_prueba(ingesta_plan, p, float(w0), int(dias_sim),
                                                   desvio, r_kcal, r_peso, 7, seed=None)
            st.session_state["txt_kcal"] = "\n".join(f"{d}, {k:.0f}" for d, k in kcal.items())
            st.session_state["txt_peso"] = "\n".join(f"{d}, {w:.2f}" for d, w in pesos_gen)

    st.caption("Puedes editar los datos a mano: una linea por registro con el formato  dia, valor  "
               "(usa punto para los decimales).")
    cA, cB = st.columns(2)
    with cA:
        st.subheader("Calorias reales por dia")
        txt_kcal = st.text_area("dia, kcal", key="txt_kcal", height=260)
    with cB:
        st.subheader("Pesos reales (dia 0 = inicial)")
        txt_peso = st.text_area("dia, peso_kg", key="txt_peso", height=260)

    kcal_pares, err_k = parsear_pares(txt_kcal)
    peso_pares, err_p = parsear_pares(txt_peso)
    for e in err_k + err_p:
        st.warning(e)
    kcal_reales = {d: v for d, v in kcal_pares}
    pesos = list(peso_pares)

    try:
        res = ejecutar_ciclo(p, float(w0), float(w_obj), int(dias), kcal_reales, pesos, float(tol))
    except Exception as e:  # noqa: BLE001
        st.error(f"No se pudo ejecutar el ciclo: {e}")
        return

    # ---- 1. Planeacion -----------------------------------------------------
    st.header("1. Planeacion (Secante + Euler)")
    m = st.columns(5)
    m[0].metric("TMB inicial", f"{res['tmb0']:.0f} kcal")
    m[1].metric("TDEE inicial", f"{res['tdee0']:.0f} kcal")
    m[2].metric("Ingesta recomendada", f"{res['ingesta']:.0f} kcal/dia")
    m[3].metric("Proteina / Grasa", f"{res['macros']['proteina_g']:.0f} g / {res['macros']['grasa_g']:.0f} g")
    m[4].metric("Carbohidratos", f"{res['macros']['carbohidratos_g']:.0f} g")
    for a in advertencias(res):
        st.warning(a)
    with st.expander("Iteraciones de la Secante"):
        filas = ["| n | kcal (x_n) | f(x_n) = peso final - meta |", "|---|---|---|"]
        filas += [f"| {n} | {x:.4f} | {fx:.6f} |" for n, x, fx in res["hist_secante"]]
        st.markdown("\n".join(filas))

    # ---- 2. Seguimiento ----------------------------------------------------
    st.header("2. Seguimiento")
    k = st.columns(4)
    d = res["d_kcal"]
    k[0].metric(f"Peso ideal dia {d}", f"{res['ideal'][d]:.2f} kg")
    k[1].metric(f"Peso por adherencia dia {d}", f"{res['adher'][d]:.2f} kg",
                f"{res['adher'][d] - res['ideal'][d]:+.2f} kg vs ideal", delta_color="inverse")
    if res["proyectado"] is not None:
        k[2].metric(f"Proyeccion real dia {res['dias']}", f"{res['proyectado']:.2f} kg",
                    f"{res['desviacion']:+.2f} kg vs meta", delta_color="inverse")
    if res["dia_cruce"] is None:
        k[3].metric("Llegada a la meta (adherencia)", "> 180 dias de retraso")
    else:
        k[3].metric("Llegada a la meta (adherencia)", f"dia {res['dia_cruce']}",
                    f"{res['dia_cruce'] - res['dias']:+d} dias vs plazo", delta_color="inverse")

    f1 = graficar_pesos(res)
    st.pyplot(f1)
    plt.close(f1)
    f2 = graficar_calorias(res)
    st.pyplot(f2)
    plt.close(f2)

    # ---- 3. Re-planeacion --------------------------------------------------
    st.header("3. Re-planeacion")
    if res["nuevo"]:
        n = res["nuevo"]
        st.error(f"La tendencia real proyecta {res['proyectado']:.2f} kg al dia {res['dias']} "
                 f"({res['desviacion']:+.2f} kg de la meta, tolerancia {res['tolerancia']} kg). "
                 "Se reinicia el ciclo.")
        r = st.columns(4)
        r[0].metric("Peso real actual", f"{n['peso_actual']:.2f} kg", f"dia {n['dia_inicio']}")
        r[1].metric("Dias restantes", n["dias_restantes"])
        r[2].metric("Nueva ingesta", f"{n['ingesta']:.0f} kcal/dia",
                    f"{n['ingesta'] - res['ingesta']:+.0f} vs original")
        r[3].metric("Proteina / Grasa / Carbo",
                    f"{n['macros']['proteina_g']:.0f} / {n['macros']['grasa_g']:.0f} / "
                    f"{n['macros']['carbohidratos_g']:.0f} g")
    elif res["proyectado"] is None:
        st.info("Registra al menos 2 pesos en dias distintos para calcular la tendencia.")
    else:
        st.success("La tendencia real esta dentro de la tolerancia: se mantiene el plan.")


# ----------------------------------------------------------------------------
def _en_streamlit() -> bool:
    import logging
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        # Se silencia el aviso "missing ScriptRunContext" (inofensivo al ejecutar con `python app.py`)
        logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)
        return get_script_run_ctx() is not None
    except Exception:  # noqa: BLE001
        return False


def _lanzar():
    faltan = [pip for mod, pip in [("numpy", "numpy"), ("matplotlib", "matplotlib"),
                                   ("streamlit", "streamlit")] if importlib.util.find_spec(mod) is None]
    if faltan:
        print("\nFaltan librerias:", ", ".join(faltan))
        print("Instalalas con:\n")
        print(f'    "{sys.executable}" -m pip install -r requirements.txt\n')
        return
    print(f"MacroSolver {__version__}: abriendo la interfaz en el navegador (Ctrl+C para cerrar)...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__], check=False)
    except KeyboardInterrupt:
        pass


if _en_streamlit():
    interfaz()
elif __name__ == "__main__":
    _lanzar()
