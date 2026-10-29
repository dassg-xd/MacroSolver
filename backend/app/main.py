import httpx
from fastapi import FastAPI

from app.services.configuracion import configuraciones
from app.services.configSupabase import crear_cliente_supabase
from app.services.securityConfig import configurar_cors
from app.routes.auth import router as auth_router

app = FastAPI(title="MacroSolver")
configurar_cors(app)
app.include_router(auth_router)

@app.get("/")
def raiz():
    return {
        "servicio": "MacroSolver",
        "health": "/health",
        "docs": "/docs",
    }

@app.get("/health")
def health():
    crear_cliente_supabase()
    url = configuraciones.supabase_url.rstrip("/")
    try:
        respuesta = httpx.get(
            f"{url}/auth/v1/health",
            headers={"apikey": configuraciones.supabase_key},
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
