import type { ReactNode } from "react";
import { CircleAlert, Inbox, type LucideIcon } from "lucide-react";

import "../styles/EstadoPantalla.css";

type TipoEstado = "cargando" | "error" | "vacio";

interface Props {
    tipo: TipoEstado;
    titulo: string;
    children?: ReactNode;
    accion?: ReactNode;
}

export default function EstadoPantalla({
    tipo,
    titulo,
    children,
    accion,
}: Props) {
    const rol = tipo === "cargando" ? "status" : tipo === "error" ? "alert" : undefined;
    const Icono: LucideIcon | null =
        tipo === "error" ? CircleAlert : tipo === "vacio" ? Inbox : null;

    return (
        <section
            className={`estado-pantalla estado-pantalla--${tipo}`}
            role={rol}
            aria-busy={tipo === "cargando" ? true : undefined}
        >
            <h2>
                {Icono && <Icono className="icono-ui" size={20} aria-hidden="true" />}
                {titulo}
            </h2>
            {children && <div className="estado-pantalla__detalle">{children}</div>}
            {accion && <div className="estado-pantalla__accion">{accion}</div>}
        </section>
    );
}
