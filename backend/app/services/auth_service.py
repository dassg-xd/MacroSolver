from typing import Any, Mapping

from app.repositories.usuario_repository import (
    CorreoYaRegistradoError,
    UsuarioRepository,
)

from app.services.security import (
    crear_access_token,
    hash_contrasena,
    verificar_contrasena,
)


class ErrorAutenticacion(Exception):
    def __init__(self, mensaje: str, status_code: int) -> None:
        super().__init__(mensaje)
        self.status_code = status_code


class AuthService:
    def __init__(self, usuarios: UsuarioRepository | None = None) -> None:
        self.usuarios = usuarios or UsuarioRepository()

    def registrar(
        self,
        correo: str,
        contrasena: str,
        perfil: Mapping[str, Any],
    ) -> dict[str, Any]:
        correo_normalizado = correo.strip().lower()

        if self.usuarios.buscar_por_correo(correo_normalizado):
            raise ErrorAutenticacion("El correo ya está registrado.", 409)

        hash = hash_contrasena(contrasena)

        try:
            usuario = self.usuarios.crear(
                correo=correo_normalizado,
                hash_contrasena=hash,
                perfil=perfil,
            )
        except CorreoYaRegistradoError as error:
            # La restricción UNIQUE de la base de datos también cubre
            # solicitudes concurrentes que pasan la búsqueda inicial.
            raise ErrorAutenticacion(
                "El correo ya está registrado.",
                409,
            ) from error

        return self._respuesta_con_token(usuario)

    def iniciar_sesion(
        self,
        correo: str,
        contrasena: str,
    ) -> dict[str, Any]:
        usuario = self.usuarios.buscar_por_correo(correo.strip().lower())

        if usuario is None or not verificar_contrasena(
            contrasena,
            usuario["hash_contrasena"],
        ):
            raise ErrorAutenticacion("Correo o contraseña incorrectos.", 401)

        usuario_publico = {
            clave: valor
            for clave, valor in usuario.items()
            if clave != "hash_contrasena"
        }

        return self._respuesta_con_token(usuario_publico)

    @staticmethod
    def _respuesta_con_token(usuario: dict[str, Any]) -> dict[str, Any]:
        usuario_publico = {
            clave: valor
            for clave, valor in usuario.items()
            if clave != "hash_contrasena"
        }

        return {
            "access_token": crear_access_token(str(usuario_publico["id"])),
            "token_type": "bearer",
            "usuario": usuario_publico,
        }