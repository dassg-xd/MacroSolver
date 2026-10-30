import { Navigate, Route, Routes } from "react-router-dom";
import Login from "../features/auth/Login";
import Registro from "../features/auth/Registro";

export function RutasApp() {
    return (
      <Routes>
        <Route path="/" element={<Registro />} />
        <Route path="/registro" element={<Registro />} />
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    );
}