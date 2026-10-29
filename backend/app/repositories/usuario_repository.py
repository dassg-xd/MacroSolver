from typing import Any, Mapping
from postgrest import APIError
from app.services.configSupabase import cliente_supabase

class CorreoYaRegistradoError(Exception):
    pass

class UsuarioRepository:
    _COLUMNAS_PUBLICAS = (
        "id, correo, nombre, sexo, fecha_nacimiento, altura_cm, "
        "factor_actividad, nivel_entrenamiento, creado_en"
    )
    
    def buscar_por_correo(self, correo: str) -> dict[str, Any] | None:
        respuesta = (
            cliente_supabase.table("usuario")
            .select(f"{self._COLUMNAS_PUBLICAS}, hash_contrasena")
            .eq("correo", correo)
            .limit(1)
            .execute()
        )
        
        return respuesta.data[0] if respuesta.data else None
    
    def crear(
        self, 
        correo: str,
        hash_contrasena: str,
        perfil: Mapping[str, Any]
    )  -> dict[str, Any]:
        datos = {
            "correo": correo,
            "hash_contrasena": hash_contrasena,
            "nombre": perfil["nombre"],
            "sexo": perfil["sexo"],
            "fecha_nacimiento": perfil["fecha_nacimiento"],
            "altura_cm": perfil["altura_cm"],
            "factor_actividad": perfil["factor_actividad"],
        }

        if "nivel_entrenamiento" in perfil:
            datos["nivel_entrenamiento"] = perfil["nivel_entrenamiento"]

        try:
            respuesta = (
                cliente_supabase.table("usuario")
                .insert(datos)
                .select(self._COLUMNAS_PUBLICAS)
                .single()
                .execute()
            )
        except APIError as error:
            if error.code == "23505":
                raise CorreoYaRegistradoError from error
            raise

        if not respuesta.data:
            raise RuntimeError("Supabase no devolvió el usuario creado.")

        return respuesta.data