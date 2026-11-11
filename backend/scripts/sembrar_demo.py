"""Carga un usuario de demostración con 30 días de registros en Supabase.

Uso (desde backend/, con el entorno activado):

    python -m scripts.sembrar_demo

Crea (o reinicia) el usuario DEMO_CORREO con un plan que empezó hace 30 días:
calorías variadas casi todos los días, pesos cada 2 o 3 días que bajan cerca del
plan y actividad física tres o cuatro veces por semana. Se puede correr las
veces que haga falta: borra los planes anteriores de ese usuario y vuelve a
anclar todo a la fecha de hoy. No toca a ningún otro usuario.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from macrosolver import (Perfil, calcular_ingesta_meta, estimar_grasa, evaluar_viabilidad, macros,
                         simular_adherencia)

from app.services.configSupabase import cliente_supabase as bd
from app.services.security import hash_contrasena

# Cuenta solo para demostraciones. Cámbiala aquí si el proyecto se publica.
DEMO_CORREO = "demo@macrosolver.app"
DEMO_CONTRASENA = "DemoMacro2026"
DEMO_NOMBRE = "Camila Demo"

DIAS = 30                 # días transcurridos del plan
PLAZO = 90                # duración del plan
PESO_INICIAL = 78.0
PESO_META = 72.0
PERFIL = {"sexo": "Femenino", "fecha_nacimiento": "1998-03-14", "altura_cm": 166.0,
          "factor_actividad": 1.55, "nivel_entrenamiento": "intermedio"}
EDAD = 28
MEDIDAS = {"cuello_cm": 33.0, "cintura_cm": 82.0, "cadera_cm": 102.0}


def _usuario() -> int:
    """Devuelve el id del usuario demo; lo crea si no existe y borra sus planes."""
    fila = bd.table("usuario").select("id").eq("correo", DEMO_CORREO).limit(1).execute().data
    datos = {"correo": DEMO_CORREO, "hash_contrasena": hash_contrasena(DEMO_CONTRASENA),
             "nombre": DEMO_NOMBRE, **PERFIL}
    if fila:
        usuario_id = int(fila[0]["id"])
        bd.table("usuario").update(datos).eq("id", usuario_id).execute()
        # Los registros se borran en cascada con el plan.
        bd.table("plan").delete().eq("usuario_id", usuario_id).execute()
        return usuario_id
    return int(bd.table("usuario").insert(datos).execute().data[0]["id"])


def _registros(ingesta: float, rnd: random.Random, inicio: date) -> tuple[dict[int, float], dict[int, list[tuple[int, int]]]]:
    """Calorías por día y actividades por día: una persona constante, no perfecta."""
    calorias: dict[int, float] = {}
    actividades: dict[int, list[tuple[int, int]]] = {}
    for i in range(DIAS + 1):
        dia_semana = (inicio + timedelta(days=i)).weekday()      # lunes = 0
        if i in (9, 22):                                         # dos días sin registrar
            continue
        if dia_semana == 5:                                      # sábado: comida fuera
            kcal = ingesta + rnd.uniform(280, 520)
        elif dia_semana == 6:
            kcal = ingesta + rnd.uniform(60, 240)
        else:
            kcal = ingesta + rnd.uniform(-190, 110)
        calorias[i] = float(round(kcal / 10) * 10)
        if dia_semana in (0, 2, 4):
            actividades[i] = [(5, rnd.choice([45, 50, 60]))]     # 5 = Pesas
        elif dia_semana == 6 and rnd.random() < 0.7:
            actividades[i] = [(1, rnd.choice([40, 60]))]         # 1 = Caminata
    return calorias, actividades


def main() -> None:
    hoy = date.today()
    inicio = hoy - timedelta(days=DIAS)
    rnd = random.Random(2026)

    perfil = Perfil("mujer", EDAD, PERFIL["altura_cm"], PERFIL["factor_actividad"])
    comp = estimar_grasa(perfil, PESO_INICIAL, MEDIDAS["cuello_cm"], MEDIDAS["cintura_cm"], MEDIDAS["cadera_cm"])
    via = evaluar_viabilidad(comp.F0, comp.L0, perfil, PESO_META, PLAZO)
    if not via.viable:
        raise SystemExit(f"El plan de demostración no es viable: {via.mensaje}")
    ingesta = round(calcular_ingesta_meta(comp.F0, comp.L0, perfil, PLAZO, PESO_META, via.i_rapida).raiz, 1)
    m = macros(ingesta, comp.L0)

    usuario_id = _usuario()
    plan = bd.table("plan").insert({
        "usuario_id": usuario_id, "fecha_inicio": inicio.isoformat(), "plazo_dias": PLAZO,
        "peso_inicial_kg": PESO_INICIAL, "peso_objetivo_kg": PESO_META, "ingesta_kcal": ingesta,
        "proteina_g": round(m.proteina_g, 1), "grasa_g": round(m.grasa_g, 1),
        "carbohidratos_g": round(m.carbohidratos_g, 1),
        "sexo": PERFIL["sexo"], "edad_anios": EDAD, "altura_cm": PERFIL["altura_cm"],
        "factor_actividad": PERFIL["factor_actividad"], **MEDIDAS,
        "pct_grasa": round(comp.pct_grasa, 1), "grasa_inicial_kg": round(comp.F0, 2),
        "masa_libre_inicial_kg": round(PESO_INICIAL - round(comp.F0, 2), 2),
        "metodo_grasa": comp.metodo, "tolerancia_kg": 1.0, "estado": "activo",
    }).execute().data[0]
    plan_id = int(plan["id"])

    calorias, actividades = _registros(ingesta, rnd, inicio)
    # Los pesos siguen la simulación con lo que de verdad comió, más el ruido normal de la báscula.
    simulado = simular_adherencia(comp.F0, comp.L0, perfil, ingesta, DIAS, calorias).W
    pesos = {i: round(simulado[i] - 0.15 + rnd.uniform(-0.3, 0.3), 1)
             for i in list(range(2, DIAS, 3)) + [DIAS]}

    def fecha(i: int) -> str:
        return (inicio + timedelta(days=i)).isoformat()

    bd.table("registro_calorias").insert(
        [{"plan_id": plan_id, "fecha": fecha(i), "kcal": k} for i, k in calorias.items()]).execute()
    bd.table("registro_peso").insert(
        [{"plan_id": plan_id, "fecha": fecha(i), "peso_kg": p} for i, p in pesos.items()]).execute()
    bd.table("registro_actividad").insert(
        [{"plan_id": plan_id, "fecha": fecha(i), "actividad_id": a, "minutos": mins}
         for i, lista in actividades.items() for a, mins in lista]).execute()

    print(f"Usuario demo listo: {DEMO_CORREO} (la contraseña está en este script).")
    print(f"Plan {plan_id}: {PESO_INICIAL} -> {PESO_META} kg en {PLAZO} días, desde {inicio}; "
          f"ingesta {ingesta:.0f} kcal.")
    print(f"Registros: {len(calorias)} días de calorías, {len(pesos)} pesos "
          f"(último {pesos[DIAS]} kg), {sum(len(a) for a in actividades.values())} actividades.")


if __name__ == "__main__":
    main()
