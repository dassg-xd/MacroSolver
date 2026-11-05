import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { EVENTO_SESION_EXPIRADA } from "../../api/clienteAxios";
import type {
    DatosLogin,
    DatosPerfil,
    DatosRegistro,
    UsuarioPublico,
} from "../../types/auth";
import { ContextoSesion } from "./SesionContext";
import {
    actualizarPerfil as apiActualizarPerfil,
    guardarUsuario,
    iniciarSesion as apiIniciarSesion,
    limpiarSesion,
    obtenerPerfil,
    registrarUsuario as apiRegistrarUsuario,
    tokenGuardado,
} from "./services/authService";

export function SesionProvider({ children }: { children: ReactNode }) {
    const [usuario, setUsuario] = useState<UsuarioPublico | null>(null);
    const [cargando, setCargando] = useState(() => Boolean(tokenGuardado()));
    const [avisoSesion, setAvisoSesion] = useState("");

    useEffect(() => {
        const token = tokenGuardado();
        if (!token) {
            return;
        }

        let vigente = true;

        obtenerPerfil()
            .then((perfil) => {
                if (!vigente) {
                    return;
                }
                guardarUsuario(perfil);
                setUsuario(perfil);
            })
            .catch(() => {
                if (!vigente) {
                    return;
                }
                limpiarSesion();
                setUsuario(null);
            })
            .finally(() => {
                if (vigente) {
                    setCargando(false);
                }
            });

        return () => {
            vigente = false;
        };
    }, []);

    useEffect(() => {
        function alExpirarSesion(evento: Event) {
            const detalle = (evento as CustomEvent<string>).detail;
            limpiarSesion();
            setUsuario(null);
            setAvisoSesion(
                detalle || "Tu sesión expiró. Inicia sesión de nuevo."
            );
        }

        window.addEventListener(EVENTO_SESION_EXPIRADA, alExpirarSesion);
        return () =>
            window.removeEventListener(
                EVENTO_SESION_EXPIRADA,
                alExpirarSesion
            );
    }, []);

    const iniciarSesion = useCallback(async (datos: DatosLogin) => {
        const respuesta = await apiIniciarSesion(datos);
        setUsuario(respuesta.usuario);
        setAvisoSesion("");
        return respuesta.usuario;
    }, []);

    const registrar = useCallback(async (datos: DatosRegistro) => {
        const respuesta = await apiRegistrarUsuario(datos);
        setUsuario(respuesta.usuario);
        setAvisoSesion("");
        return respuesta.usuario;
    }, []);

    const cerrarSesion = useCallback(() => {
        limpiarSesion();
        setUsuario(null);
        setAvisoSesion("");
    }, []);

    const actualizarPerfil = useCallback(async (datos: DatosPerfil) => {
        const perfil = await apiActualizarPerfil(datos);
        guardarUsuario(perfil);
        setUsuario(perfil);
        return perfil;
    }, []);

    const limpiarAviso = useCallback(() => setAvisoSesion(""), []);

    const valor = useMemo(
        () => ({
            usuario,
            cargando,
            avisoSesion,
            iniciarSesion,
            registrar,
            cerrarSesion,
            actualizarPerfil,
            limpiarAviso,
        }),
        [
            usuario,
            cargando,
            avisoSesion,
            iniciarSesion,
            registrar,
            cerrarSesion,
            actualizarPerfil,
            limpiarAviso,
        ]
    );

    return (
        <ContextoSesion.Provider value={valor}>
            {children}
        </ContextoSesion.Provider>
    );
}
