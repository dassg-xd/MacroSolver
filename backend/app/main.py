"""API de MacroSolver.

Arranque normal (desde backend/):  uvicorn app.main:app --reload
También se puede ejecutar este archivo directamente (botón ▶ de VS Code):
lanza uvicorn con el Python de backend/.venv aunque el intérprete elegido sea otro.
"""
import os
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    _BACKEND = Path(__file__).resolve().parents[1]
    _VENV = _BACKEND / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    _PYTHON = str(_VENV) if _VENV.exists() else sys.executable
    print(f"Iniciando MacroSolver con {_PYTHON}", flush=True)
    print("API: http://127.0.0.1:8000  ·  Documentación: http://127.0.0.1:8000/docs", flush=True)
    sys.exit(
        subprocess.call(
            [_PYTHON, "-m", "uvicorn", "app.main:app", "--reload", "--reload-dir", "app"],
            cwd=_BACKEND,
        )
    )

import httpx
from fastapi import FastAPI

from app.services.configuracion import configuraciones
from app.services.securityConfig import configurar_cors
from app.errores import registrar_manejadores
from app.routes.auth import router as auth_router
from app.routes.planes import router as planes_router
from app.routes.registros import router as registros_router
from app.routes.seguimiento import router as seguimiento_router
from app.routes.usuario import router as usuario_router

app = FastAPI(title="MacroSolver")
configurar_cors(app)
registrar_manejadores(app)
app.include_router(auth_router)
app.include_router(usuario_router)
app.include_router(planes_router)
app.include_router(registros_router)
app.include_router(seguimiento_router)

@app.get("/")
def raiz():
    return {
        "servicio": "MacroSolver",
        "health": "/health",
        "docs": "/docs",
    }

@app.get("/health")
def health():
    url = configuraciones.supabase_url.rstrip("/")
    try:
        respuesta = httpx.get(
            f"{url}/auth/v1/health",
            headers={"apikey": configuraciones.supabase_secret_key},
            timeout=10.0,
        )
        supabase_ok = respuesta.status_code == 200
        detalle = None if supabase_ok else f"HTTP {respuesta.status_code}"
    except httpx.HTTPError as error:
        supabase_ok = False
        detalle = str(error)

    return {
        "ok": supabase_ok,
        "supabase": supabase_ok,
        "detalle": detalle,
    }
