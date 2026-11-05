import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "../components/Layout";
import Login from "../features/auth/Login";
import Registro from "../features/auth/Registro";
import Bienvenida from "../features/panel/Bienvenida";
import Panel from "../features/panel/Panel";
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
                <Route path="/bienvenida" element={<Bienvenida />} />
            </Route>

            <Route path="/" element={<Navigate to="/panel" replace />} />
            <Route path="*" element={<Navigate to="/panel" replace />} />
        </Routes>
    );
}
