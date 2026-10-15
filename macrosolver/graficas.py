"""Graficas (matplotlib)."""
from __future__ import annotations

import numpy as np

from .modelo import tdee

# Colores aptos para daltonismo
C_IDEAL, C_ADHER, C_REAL, C_TEND, C_REPLAN, C_META = (
    "#0072B2", "#D55E00", "#000000", "#CC79A7", "#009E73", "#7f7f7f",
)


def graficar_pesos(res: dict):
    import matplotlib.pyplot as plt
    dias, dk = res["dias"], res["d_kcal"]
    x = np.arange(dias + 1)
    fig, ax = plt.subplots(figsize=(10, 5.4))

    ax.plot(x, res["ideal"], color=C_IDEAL, lw=2.2, label="Curva ideal (Euler + Secante)")
    ax.plot(x[:dk + 1], res["adher"][:dk + 1], color=C_ADHER, lw=2.2,
            label="Simulacion por adherencia (Euler, kcal reales)")
    if dk < dias:
        ax.plot(x[dk:], res["adher"][dk:], color=C_ADHER, lw=2.0, ls=":",
                label="Proyeccion si retoma el plan")
    if res["pesos"]:
        ax.scatter([d for d, _ in res["pesos"]], [w for _, w in res["pesos"]], color=C_REAL,
                   zorder=5, s=42, label="Peso real registrado")
    if res["C"] is not None:
        ax.plot(x, res["C"] * np.exp(res["A"] * x), color=C_TEND, lw=2.0, ls="--",
                label=f"Tendencia real (minimos cuadrados: {res['C']:.1f}·e^({res['A']:.5f}·x))")
    if res["nuevo"]:
        n = res["nuevo"]
        ax.plot(n["dia_inicio"] + np.arange(n["dias_restantes"] + 1), n["curva"], color=C_REPLAN, lw=2.4,
                ls="-.", label=f"Re-planeacion ({n['ingesta']:.0f} kcal/dia)")
    ax.axhline(res["w_obj"], color=C_META, lw=1.2)
    ax.annotate(f"Meta {res['w_obj']:.1f} kg", (0, res["w_obj"]), textcoords="offset points",
                xytext=(4, 5), color=C_META, fontsize=9)
    ax.axvline(dias, color=C_META, lw=0.8, ls=":")
    ax.set_xlabel("Dia")
    ax.set_ylabel("Peso (kg)")
    ax.set_title("Evolucion del peso: ideal, adherencia, realidad y re-planeacion")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8.5, loc="best")
    fig.tight_layout()
    return fig


def graficar_calorias(res: dict):
    import matplotlib.pyplot as plt
    p, dias = res["perfil"], res["dias"]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    kr = res["kcal_reales"]
    if kr:
        ds = sorted(d for d in kr if d <= dias)
        ax.bar(ds, [kr[d] for d in ds], color=C_ADHER, alpha=0.45, label="Kcal reales consumidas")
    x = np.arange(1, dias + 1)
    gasto = [tdee(w, p) for w in res["adher"][:-1]]
    ax.plot(x, gasto, color=C_REAL, lw=2.0, label="TDEE (baja al perder peso: adaptacion metabolica)")
    ax.hlines(res["ingesta"], 1, dias, color=C_IDEAL, lw=2.2,
              label=f"Ingesta recomendada ({res['ingesta']:.0f} kcal)")
    if res["nuevo"]:
        n = res["nuevo"]
        ax.hlines(n["ingesta"], n["dia_inicio"] + 1, dias, color=C_REPLAN, lw=2.4, ls="-.",
                  label=f"Nueva ingesta re-planeada ({n['ingesta']:.0f} kcal)")
    ax.set_xlabel("Dia")
    ax.set_ylabel("kcal / dia")
    ax.set_title("Calorias: lo recomendado, lo consumido y el gasto energetico")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8.5, loc="best")
    fig.tight_layout()
    return fig
