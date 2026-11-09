import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "../components/Layout";
import Login from "../features/auth/Login";
import Registro from "../features/auth/Registro";
import Calendario from "../features/calendario/Calendario";
import Panel from "../features/panel/Panel";
import Bienvenida from "../features/panel/Bienvenida";
import NuevoPlan from "../features/plan/NuevoPlan";
import PantallaCalculo from "../features/plan/PantallaCalculo";
import Perfil from "../features/perfil/Perfil";
import { RutaProtegida, RutaPublica } from "./RutaProtegida";

export function RutasApp() {
    return (
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
                <Route path="/nuevo-plan" element={<NuevoPlan />} />
                <Route path="/plan/como-se-calculo" element={<PantallaCalculo />} />
                <Route path="/bienvenida" element={<Bienvenida />} />
            </Route>

            <Route path="/" element={<Navigate to="/panel" replace />} />
            <Route path="*" element={<Navigate to="/panel" replace />} />
        </Routes>
    );
}
