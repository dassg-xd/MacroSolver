import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import EsqueletoPagina from "../components/Esqueleto";
import { useSesion } from "../features/auth/SesionContext";

export function RutaProtegida({ children }: { children: ReactNode }) {
    const { usuario, cargando, avisoSesion } = useSesion();
    const ubicacion = useLocation();

    if (cargando) {
        return <EsqueletoPagina mensaje="Cargando tu sesión..." />;
    }

    if (!usuario) {
        return (
            <Navigate
                to="/login"
                replace
                state={{
                    desde: `${ubicacion.pathname}${ubicacion.search}`,
                    aviso: avisoSesion,
                }}
            />
        );
    }

    return <>{children}</>;
}

export function RutaPublica({ children }: { children: ReactNode }) {
    const { usuario, cargando } = useSesion();

    if (cargando) {
        return (
            <EsqueletoPagina
                tipo="autenticacion"
                mensaje="Cargando tu sesión..."
            />
        );
    }

    if (usuario) {
        return <Navigate to="/panel" replace />;
    }

    return <>{children}</>;
}
