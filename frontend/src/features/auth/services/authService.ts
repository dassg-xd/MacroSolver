import { clienteAxios } from "../../../api";
import type {
    DatosLogin,
    DatosPerfil,
    DatosRegistro,
    RespuestaAuth,
    UsuarioPublico,
} from "../../../types/auth";

const CLAVE_TOKEN = "auth_token";
const CLAVE_USUARIO = "auth_usuario";

export function guardarSesion(respuesta: RespuestaAuth): void {
    localStorage.setItem(CLAVE_TOKEN, respuesta.access_token);
    localStorage.setItem(CLAVE_USUARIO, JSON.stringify(respuesta.usuario));
}

export function guardarUsuario(usuario: UsuarioPublico): void {
    localStorage.setItem(CLAVE_USUARIO, JSON.stringify(usuario));
}

export function limpiarSesion(): void {
    localStorage.removeItem(CLAVE_TOKEN);
    localStorage.removeItem(CLAVE_USUARIO);
}

export function tokenGuardado(): string | null {
    return localStorage.getItem(CLAVE_TOKEN);
}

export function usuarioGuardado(): UsuarioPublico | null {
    const guardado = localStorage.getItem(CLAVE_USUARIO);
    if (!guardado) {
        return null;
    }

    try {
        return JSON.parse(guardado) as UsuarioPublico;
    } catch {
        limpiarSesion();
        return null;
    }
}

export const registrarUsuario = async (
    data: DatosRegistro
): Promise<RespuestaAuth> => {
    const response = await clienteAxios.post<RespuestaAuth>(
        "/auth/registro",
        data
    );

    guardarSesion(response.data);
    return response.data;
};

export const iniciarSesion = async (
    data: DatosLogin
): Promise<RespuestaAuth> => {
    const response = await clienteAxios.post<RespuestaAuth>(
        "/auth/login",
        data
    );

    guardarSesion(response.data);
    return response.data;
};

export const obtenerPerfil = async (): Promise<UsuarioPublico> => {
    const response = await clienteAxios.get<UsuarioPublico>("/me");
    return response.data;
};

export const actualizarPerfil = async (
    data: DatosPerfil
): Promise<UsuarioPublico> => {
    const response = await clienteAxios.patch<UsuarioPublico>("/me", data);
    return response.data;
};
