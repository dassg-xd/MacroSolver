import httpx
from fastapi import FastAPI

from app.services.configuracion import configuraciones
from app.services.securityConfig import configurar_cors
from app.errores import registrar_manejadores
from app.routes.auth import router as auth_router
from app.routes.usuario import router as usuario_router

app = FastAPI(title="MacroSolver")
configurar_cors(app)
registrar_manejadores(app)
app.include_router(auth_router)
app.include_router(usuario_router)

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
