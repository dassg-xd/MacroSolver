"""Los errores llegan al frontend en español, en 'detail', con un 'codigo' estable."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errores import registrar_manejadores
from app.main import app
from macrosolver import ErrorMotor

cliente = TestClient(app)

REGISTRO = {
    "correo": "ana@correo.com",
    "contrasena": "clave-segura1",
    "nombre": "Ana",
    "sexo": "Femenino",
    "fecha_nacimiento": "1995-04-12",
    "altura_cm": 165,
    "factor_actividad": "1.55",
}


def registrar(**cambios):
    return cliente.post("/auth/registro", json={**REGISTRO, **cambios})


def test_correo_mal_escrito():
    r = registrar(correo="ana-arroba-correo")
    assert r.status_code == 422
    assert r.json()["detail"] == "El correo no tiene un formato válido."
    assert r.json()["errores"][0]["campo"] == "correo"


def test_contrasena_corta():
    r = registrar(contrasena="123")
    assert r.status_code == 422
    assert r.json()["detail"] == "La contraseña debe tener al menos 8 caracteres."


def test_campo_faltante_y_valor_fuera_de_rango():
    datos = dict(REGISTRO)
    del datos["nombre"]
    datos["altura_cm"] = 90
    r = cliente.post("/auth/registro", json=datos)
    cuerpo = r.json()
    assert r.status_code == 422
    assert cuerpo["codigo"] == "datos_invalidos"
    assert {e["campo"] for e in cuerpo["errores"]} == {"nombre", "altura_cm"}
    assert "Nombre: es obligatorio." in cuerpo["detail"]
    assert "Altura (cm): debe ser mayor o igual que 100." in cuerpo["detail"]


def test_sexo_no_permitido():
    r = registrar(sexo="otro")
    assert r.status_code == 422
    assert r.json()["detail"].startswith("Sexo: debe ser una de estas opciones")


def _app_de_prueba() -> TestClient:
    prueba = FastAPI()
    registrar_manejadores(prueba)

    @prueba.get("/motor")
    def motor():
        raise ErrorMotor("meta_no_es_perdida", "La meta debe ser menor que el peso inicial.")

    @prueba.get("/falla")
    def falla():
        raise RuntimeError("detalle interno que no debe salir")

    return TestClient(prueba, raise_server_exceptions=False)


def test_error_del_motor_es_422_con_codigo():
    r = _app_de_prueba().get("/motor")
    assert r.status_code == 422
    assert r.json() == {"detail": "La meta debe ser menor que el peso inicial.",
                        "codigo": "meta_no_es_perdida"}


def test_error_inesperado_no_filtra_detalles():
    r = _app_de_prueba().get("/falla")
    assert r.status_code == 500
    assert "detalle interno" not in r.text
    assert r.json()["codigo"] == "error_interno"
