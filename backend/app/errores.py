"""Manejadores globales de errores: toda respuesta de error lleva 'detail' en español.

Forma de la respuesta:
    {"detail": "<mensaje para mostrar>", "codigo": "<código estable>", "errores": [...]}
'errores' solo aparece en errores de validación (uno por campo).
"""
import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from macrosolver import ErrorMotor

log = logging.getLogger("macrosolver.api")

NOMBRES_CAMPOS = {
    "correo": "Correo",
    "contrasena": "Contraseña",
    "nombre": "Nombre",
    "sexo": "Sexo",
    "fecha_nacimiento": "Fecha de nacimiento",
    "altura_cm": "Altura (cm)",
    "factor_actividad": "Factor de actividad",
    "nivel_entrenamiento": "Nivel de entrenamiento",
}


def _campo(loc: tuple[Any, ...]) -> str:
    """('body', 'altura_cm') → 'altura_cm'."""
    partes = [str(p) for p in loc if p not in ("body", "query", "path")]
    return ".".join(partes)


def traducir_error(error: dict[str, Any]) -> str:
    """Convierte un error de Pydantic en un mensaje en español."""
    tipo = error.get("type", "")
    ctx = error.get("ctx") or {}
    campo = _campo(tuple(error.get("loc", ())))
    nombre = NOMBRES_CAMPOS.get(campo, campo or "El dato")

    if tipo == "value_error":
        mensaje = str(error.get("msg", ""))
        if "email" in mensaje.lower():
            return "El correo no tiene un formato válido."
        return mensaje.removeprefix("Value error, ")
    if tipo == "missing":
        return f"{nombre}: es obligatorio."
    if tipo == "extra_forbidden":
        return f"{nombre}: este campo no se permite."
    if tipo == "literal_error":
        return f"{nombre}: debe ser una de estas opciones: {ctx.get('expected', '')}."
    if tipo == "string_too_short":
        return f"{nombre}: debe tener al menos {ctx.get('min_length')} caracteres."
    if tipo == "string_too_long":
        return f"{nombre}: debe tener máximo {ctx.get('max_length')} caracteres."
    if tipo in ("greater_than_equal", "greater_than"):
        limite = ctx.get("ge", ctx.get("gt"))
        return f"{nombre}: debe ser mayor{' o igual' if tipo == 'greater_than_equal' else ''} que {limite}."
    if tipo in ("less_than_equal", "less_than"):
        limite = ctx.get("le", ctx.get("lt"))
        return f"{nombre}: debe ser menor{' o igual' if tipo == 'less_than_equal' else ''} que {limite}."
    if tipo.startswith(("date_", "datetime_")):
        return f"{nombre}: no es una fecha válida (usa AAAA-MM-DD)."
    if tipo.startswith(("decimal_", "float_", "int_")):
        return f"{nombre}: debe ser un número."
    if tipo in ("string_type",):
        return f"{nombre}: debe ser texto."
    if tipo == "json_invalid":
        return "La petición no tiene un JSON válido."
    return f"{nombre}: el valor no es válido."


async def _validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
    errores = [
        {"campo": _campo(tuple(e.get("loc", ()))), "mensaje": traducir_error(e)}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "detail": " ".join(e["mensaje"] for e in errores) or "Los datos enviados no son válidos.",
            "codigo": "datos_invalidos",
            "errores": errores,
        },
    )


async def _error_motor(_: Request, exc: ErrorMotor) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": exc.mensaje, "codigo": exc.codigo},
    )


async def _inesperado(request: Request, exc: Exception) -> JSONResponse:
    log.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ocurrió un error interno. Intenta de nuevo en unos minutos.",
                 "codigo": "error_interno"},
    )


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validacion)
    app.add_exception_handler(ErrorMotor, _error_motor)
    app.add_exception_handler(Exception, _inesperado)
