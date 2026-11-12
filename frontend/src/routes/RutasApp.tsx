import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import EsqueletoPagina from "../components/Esqueleto";
import { RutaProtegida, RutaPublica } from "./RutaProtegida";

const Layout = lazy(() => import("../components/Layout"));
const Login = lazy(() => import("../features/auth/Login"));
const Registro = lazy(() => import("../features/auth/Registro"));
const Calendario = lazy(() => import("../features/calendario/Calendario"));
const Estadisticas = lazy(() => import("../features/estadisticas/Estadisticas"));
const Guia = lazy(() => import("../features/guia/Guia"));
const Historial = lazy(() => import("../features/historial/Historial"));
const Panel = lazy(() => import("../features/panel/Panel"));
const Bienvenida = lazy(() => import("../features/panel/Bienvenida"));
const NuevoPlan = lazy(() => import("../features/plan/NuevoPlan"));
const PantallaCalculo = lazy(() => import("../features/plan/PantallaCalculo"));
const Perfil = lazy(() => import("../features/perfil/Perfil"));

export function RutasApp() {
    const { pathname } = useLocation();
    const tipoEsqueleto =
        pathname === "/login" || pathname === "/registro"
            ? "autenticacion"
            : "pagina";

    return (
        <Suspense
            fallback={
                <EsqueletoPagina
                    tipo={tipoEsqueleto}
                    mensaje="Cargando la pantalla..."
                />
            }
        >
            <Routes>
                <Route
                    path="/login"
                    element={
                        <RutaPublica>
                            <Login />
                        </RutaPublica>
                    }
                />
                <Route
                    path="/registro"
                    element={
                        <RutaPublica>
                            <Registro />
                        </RutaPublica>
                    }
                />

                <Route
                    element={
                        <RutaProtegida>
                            <Layout />
                        </RutaProtegida>
                    }
                >
                    <Route path="/panel" element={<Panel />} />
                    <Route path="/perfil" element={<Perfil />} />
                    <Route path="/calendario" element={<Calendario />} />
                    <Route path="/estadisticas" element={<Estadisticas />} />
                    <Route path="/historial" element={<Historial />} />
                    <Route path="/guia" element={<Guia />} />
                    <Route path="/nuevo-plan" element={<NuevoPlan />} />
                    <Route path="/plan/como-se-calculo" element={<PantallaCalculo />} />
                    <Route path="/bienvenida" element={<Bienvenida />} />
                </Route>

                <Route path="/" element={<Navigate to="/panel" replace />} />
                <Route path="*" element={<Navigate to="/panel" replace />} />
            </Routes>
        </Suspense>
    );
}
