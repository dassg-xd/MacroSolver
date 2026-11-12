import { Link } from "react-router-dom";
import { LayoutDashboard, Plus } from "lucide-react";

import { useSesion } from "../auth/SesionContext";
import "../../styles/Panel.css";

export default function Bienvenida() {
    const { usuario } = useSesion();
    const nombre = usuario?.nombre?.split(" ")[0] ?? "";

    return (
        <section className="panel panel--angosto">
            <header className="panel__cabecera">
                <p className="panel__saludo">Cuenta lista</p>
                <h1>Bienvenido, {nombre}</h1>
                <p className="panel__bajada">
                    Ya puedes crear tu plan. Antes de confirmar verás la ingesta
                    diaria, los macros, la curva estimada y los bloqueos de
                    seguridad.
                </p>
            </header>

            <article className="panel__tarjeta">
                <span className="panel__etiqueta">Siguiente paso</span>
                <h2>Crea tu primer plan</h2>
                <p>
                    Necesitas tu peso actual, tu peso meta y las medidas de cuello y
                    cintura. La fecha de inicio es hoy por defecto y puedes
                    cambiarla.
                </p>
                <div className="panel__acciones">
                    <Link className="panel__cta" to="/nuevo-plan">
                        <Plus size={17} aria-hidden="true" />
                        Crear mi plan
                    </Link>
                    <Link className="panel__enlace" to="/panel">
                        <LayoutDashboard size={16} aria-hidden="true" />
                        Ir al panel
                    </Link>
                </div>
            </article>
        </section>
    );
}
