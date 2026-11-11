"""Repositorios en memoria y un plan de prueba coherente con el motor."""
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.dependencias import (
    obtener_repositorio_planes,
    obtener_repositorio_registros,
    obtener_repositorio_usuarios,
)
from app.main import app
from app.services.security import crear_access_token
from macrosolver import Perfil, calcular_ingesta_meta, estimar_grasa, evaluar_viabilidad, macros

USUARIO = {
    "id": 7, "correo": "ana@correo.com", "nombre": "Ana", "sexo": "Femenino",
    "fecha_nacimiento": "1995-04-12", "altura_cm": "165.0", "factor_actividad": "1.55",
    "nivel_entrenamiento": "principiante", "creado_en": "2026-11-01T10:00:00+00:00",
}
CATALOGO = [
    {"id": 1, "nombre": "Caminata", "tipo": "aerobico", "met": 3.5},
    {"id": 5, "nombre": "Pesas", "tipo": "fuerza", "met": 5.0},
]


def plan_de_prueba(inicio: date, N: int = 90, W0: float = 80.0, W_meta: float = 76.0, plan_id: int = 42) -> dict:
    perfil = Perfil("mujer", 31, 165.0, 1.55)
    comp = estimar_grasa(perfil, W0)
    via = evaluar_viabilidad(comp.F0, comp.L0, perfil, W_meta, N)
    ingesta = calcular_ingesta_meta(comp.F0, comp.L0, perfil, N, W_meta, via.i_rapida).raiz
    m = macros(ingesta, comp.L0)
    return {
        "id": plan_id, "usuario_id": 7, "plan_previo_id": None, "estado": "activo",
        "fecha_inicio": inicio.isoformat(), "plazo_dias": N,
        "peso_inicial_kg": W0, "peso_objetivo_kg": W_meta, "ingesta_kcal": round(ingesta, 1),
        "proteina_g": m.proteina_g, "grasa_g": m.grasa_g, "carbohidratos_g": m.carbohidratos_g,
        "sexo": "Femenino", "edad_anios": 31, "altura_cm": 165.0, "factor_actividad": 1.55,
        "pct_grasa": comp.pct_grasa, "grasa_inicial_kg": comp.F0, "masa_libre_inicial_kg": comp.L0,
        "metodo_grasa": comp.metodo, "tolerancia_kg": 1.0, "creado_en": "2026-10-01T10:00:00+00:00",
    }


class Usuarios:
    def buscar_por_id(self, usuario_id):
        return dict(USUARIO) if usuario_id == 7 else None


class Planes:
    def __init__(self, plan: dict | None = None):
        self.todos: list[dict] = [plan] if plan else []

    @property
    def activo(self):
        return next((p for p in self.todos if p["estado"] == "activo"), None)

    def buscar_activo(self, usuario_id):
        return self.activo

    def listar(self, usuario_id):
        return sorted(self.todos, key=lambda p: p["id"], reverse=True)

    def crear(self, usuario_id, plan):
        previo = self.activo
        if previo:
            previo["estado"] = "inactivo"
        fila = {
            "id": max((p["id"] for p in self.todos), default=0) + 1, "usuario_id": usuario_id,
            "plan_previo_id": previo["id"] if previo else None, "estado": "activo",
            "creado_en": "2026-11-05T10:00:00+00:00", **plan,
        }
        self.todos.append(fila)
        return fila


class Registros:
    """Registros por plan: {plan_id: {fecha: valor}}."""

    def __init__(self):
        self.calorias: dict[int, dict[date, float]] = {}
        self.pesos: dict[int, dict[date, float]] = {}
        self.actividades: dict[int, dict[date, list[dict]]] = {}

    def catalogo(self):
        return [dict(a) for a in CATALOGO]

    def listar(self, plan_id, desde, hasta):
        def dentro(d):
            return desde <= d <= hasta
        return {
            "calorias": [{"fecha": d.isoformat(), "kcal": k}
                         for d, k in sorted(self.calorias.get(plan_id, {}).items()) if dentro(d)],
            "pesos": [{"fecha": d.isoformat(), "peso_kg": p}
                      for d, p in sorted(self.pesos.get(plan_id, {}).items()) if dentro(d)],
            "actividades": [{"fecha": d.isoformat(), **a}
                            for d, lista in sorted(self.actividades.get(plan_id, {}).items())
                            if dentro(d) for a in lista],
        }

    def ultimo_peso_hasta(self, plan_id, fecha):
        previos = [d for d in self.pesos.get(plan_id, {}) if d <= fecha]
        return self.pesos[plan_id][max(previos)] if previos else None

    def guardar_calorias(self, plan_id, fecha, kcal):
        self.calorias.setdefault(plan_id, {})[fecha] = kcal

    def borrar_calorias(self, plan_id, fecha):
        self.calorias.get(plan_id, {}).pop(fecha, None)

    def guardar_peso(self, plan_id, fecha, peso_kg):
        self.pesos.setdefault(plan_id, {})[fecha] = peso_kg

    def borrar_peso(self, plan_id, fecha):
        self.pesos.get(plan_id, {}).pop(fecha, None)

    def reemplazar_actividades(self, plan_id, fecha, actividades):
        if actividades:
            self.actividades.setdefault(plan_id, {})[fecha] = [dict(a) for a in actividades]
        else:
            self.actividades.get(plan_id, {}).pop(fecha, None)


def cliente_con(planes: Planes, registros: Registros) -> TestClient:
    app.dependency_overrides[obtener_repositorio_usuarios] = Usuarios
    app.dependency_overrides[obtener_repositorio_planes] = lambda: planes
    app.dependency_overrides[obtener_repositorio_registros] = lambda: registros
    return TestClient(app, headers={"Authorization": f"Bearer {crear_access_token('7')}"})


def dias_atras(n: int) -> date:
    return date.today() - timedelta(days=n)
