import { clienteAxios } from "../../../api";
import type {
    DatosLogin,
    DatosRegistro,
    RespuestaAuth,
} from "../../../types/auth";

function guardarSesion(respuesta: RespuestaAuth): void {
    localStorage.setItem("auth_token", respuesta.access_token);
    localStorage.setItem("auth_usuario", JSON.stringify(respuesta.usuario));
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