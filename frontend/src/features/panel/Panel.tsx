import { Link } from "react-router-dom";

import { useSesion } from "../auth/SesionContext";
import "../../styles/Panel.css";

export default function Panel() {
    const { usuario } = useSesion();
    const nombre = usuario?.nombre?.split(" ")[0] ?? "";

    return (
        <section className="panel">
            <header className="panel__cabecera">
                <div>
                    <p className="panel__saludo">Hola, {nombre}</p>
                    <h1>Tu panel</h1>
                    <p className="panel__bajada">
                        Aquí verás el resumen de tu plan activo y el avance de la
                        semana.
                    </p>
                </div>
            </header>

            <article className="panel__tarjeta panel__tarjeta--vacia">
                <div>
                    <span className="panel__etiqueta">Plan activo</span>
                    <h2>Todavía no tienes un plan</h2>
                    <p>
                        Define tu peso meta y la fecha en la que quieres llegar.
                        Antes de confirmar verás la ingesta, los macros y la curva
                        estimada.
                    </p>
                </div>
                <Link className="panel__cta" to="/nuevo-plan">
                    Crear mi plan
                </Link>
            </article>

            <div className="panel__pasos">
                <article>
                    <strong>1</strong>
                    <h3>Completa tu perfil</h3>
                    <p>
                        Revisa tu altura, actividad y nivel de entrenamiento. Puedes
                        cambiarlos cuando quieras.
                    </p>
                    <Link to="/perfil">Ir a mi perfil</Link>
                </article>
                <article>
                    <strong>2</strong>
                    <h3>Calcula tu plan</h3>
                    <p>
                        La vista previa te muestra la viabilidad de la meta, los
                        bloqueos y cómo se calculó.
                    </p>
                    <Link to="/nuevo-plan">Nuevo plan</Link>
                </article>
                <article>
                    <strong>3</strong>
                    <h3>Registra tus días</h3>
                    <p>
                        El calendario y el seguimiento llegan en la siguiente
                        entrega de la épica 3.
                    </p>
                </article>
            </div>
        </section>
    );
}
