import { createContext, useContext } from "react";

import type {
    DatosLogin,
    DatosPerfil,
    DatosRegistro,
    UsuarioPublico,
} from "../../types/auth";

export interface SesionContexto {
    usuario: UsuarioPublico | null;
    cargando: boolean;
    avisoSesion: string;
    iniciarSesion: (datos: DatosLogin) => Promise<UsuarioPublico>;
    registrar: (datos: DatosRegistro) => Promise<UsuarioPublico>;
    cerrarSesion: () => void;
    actualizarPerfil: (datos: DatosPerfil) => Promise<UsuarioPublico>;
    limpiarAviso: () => void;
}

export const ContextoSesion = createContext<SesionContexto | null>(null);

export function useSesion(): SesionContexto {
    const contexto = useContext(ContextoSesion);
    if (!contexto) {
        throw new Error("useSesion debe usarse dentro de SesionProvider.");
    }
    return contexto;
}
