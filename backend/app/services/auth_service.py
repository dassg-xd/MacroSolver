import math
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

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


class GestorIntentosFallidos:
    """Bloqueo temporal en memoria tras varios intentos fallidos (HU-02B).

    Se guarda por correo, exista o no la cuenta, para no revelar qué correos
    están registrados. El reloj es inyectable para probar la expiración.
    """

    MAX_INTENTOS = 3
    DURACION = timedelta(minutes=15)

    def __init__(
        self,
        reloj: Callable[[], datetime] | None = None,
    ) -> None:
        self._reloj = reloj or (lambda: datetime.now(timezone.utc))
        self._fallos: dict[str, list[datetime]] = {}

    def _recientes(self, correo: str, ahora: datetime) -> list[datetime]:
        return [
            momento
            for momento in self._fallos.get(correo, [])
            if ahora - momento < self.DURACION
        ]

    def segundos_bloqueo(self, correo: str) -> int | None:
        """Segundos que faltan para desbloquear, o None si no está bloqueado."""
        ahora = self._reloj()
        recientes = self._recientes(correo, ahora)
        if recientes:
            self._fallos[correo] = recientes
        else:
            self._fallos.pop(correo, None)

        if len(recientes) < self.MAX_INTENTOS:
            return None

        restante = self.DURACION - (ahora - recientes[0])
        return max(1, math.ceil(restante.total_seconds()))

    def registrar_fallo(self, correo: str) -> None:
        ahora = self._reloj()
        recientes = self._recientes(correo, ahora)
        recientes.append(ahora)
        self._fallos[correo] = recientes

    def limpiar(self, correo: str) -> None:
        self._fallos.pop(correo, None)


class AuthService:
    def __init__(
        self,
        usuarios: UsuarioRepository | None = None,
        intentos: GestorIntentosFallidos | None = None,
    ) -> None:
        self.usuarios = usuarios or UsuarioRepository()
        self.intentos = intentos or GestorIntentosFallidos()

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
        correo_normalizado = correo.strip().lower()

        restante = self.intentos.segundos_bloqueo(correo_normalizado)
        if restante is not None:
            raise ErrorAutenticacion(self._mensaje_bloqueo(restante), 429)

        usuario = self.usuarios.buscar_por_correo(correo_normalizado)

        if usuario is None or not verificar_contrasena(
            contrasena,
            usuario["hash_contrasena"],
        ):
            self.intentos.registrar_fallo(correo_normalizado)
            restante = self.intentos.segundos_bloqueo(correo_normalizado)
            if restante is not None:
                raise ErrorAutenticacion(self._mensaje_bloqueo(restante), 429)
            raise ErrorAutenticacion("Correo o contraseña incorrectos.", 401)

        self.intentos.limpiar(correo_normalizado)
        usuario_publico = {
            clave: valor
            for clave, valor in usuario.items()
            if clave != "hash_contrasena"
        }

        return self._respuesta_con_token(usuario_publico)

    @staticmethod
    def _mensaje_bloqueo(segundos: int) -> str:
        minutos = max(1, math.ceil(segundos / 60))
        unidad = "minuto" if minutos == 1 else "minutos"
        return (
            "Demasiados intentos fallidos. "
            f"Intenta de nuevo en {minutos} {unidad}."
        )

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