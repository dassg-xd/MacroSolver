from functools import lru_cache
from supabase import Client, create_client

from app.services.configuracion import configuraciones

@lru_cache(maxsize=1)
def crear_cliente_supabase() -> Client:
    return create_client(configuraciones.supabase_url, configuraciones.supabase_secret_key)

cliente_supabase = crear_cliente_supabase()