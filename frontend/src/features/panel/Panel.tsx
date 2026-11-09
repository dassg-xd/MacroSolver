import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useSesion } from "../auth/SesionContext";
import { obtenerPlanActivo } from "../plan/planService";
import type { PlanActivo } from "../../types/plan";
import "../../styles/Panel.css";

export default function Panel() {
    const { usuario } = useSesion();
    const nombre = usuario?.nombre?.split(" ")[0] ?? "";
    const [plan, setPlan] = useState<PlanActivo | null>(null);
    const [cargando, setCargando] = useState(true);

    useEffect(() => {
        obtenerPlanActivo()
            .then(setPlan)
            .finally(() => setCargando(false));
    }, []);

    return (
        <section className="panel">
            <header className="panel__cabecera">
                <div>
                    <p className="panel__saludo">Hola, {nombre}</p>
                    <h1>Tu panel</h1>
                    <p className="panel__bajada">
                        Resumen de tu plan activo y el avance de la semana.
                    </p>
                </div>
            </header>

            {cargando && <p className="panel__cargando">Cargando tu plan...</p>}

            {!cargando && !plan && (
                <article className="panel__tarjeta panel__tarjeta--vacia">
                    <div>
                        <span className="panel__etiqueta">Plan activo</span>
                        <h2>Todavía no tienes un plan</h2>
                        <p>
                            Define tu peso meta y la fecha en la que quieres
                            llegar. Antes de confirmar verás la ingesta, los
                            macros y la curva estimada.
                        </p>
                    </div>
                    <Link className="panel__cta" to="/nuevo-plan">
                        Crear mi plan
                    </Link>
                </article>
            )}

            {!cargando && plan && (
                <article className="panel__tarjeta">
                    <div>
                        <span className="panel__etiqueta">Plan activo</span>
                        <h2>
                            {plan.ingesta_kcal.toFixed(0)} kcal / día
                        </h2>
                        <p>
                            Meta {plan.peso_objetivo_kg.toFixed(1)} kg · fecha{" "}
                            {plan.fecha_meta} · {plan.dias_restantes} días
                            restantes.
                        </p>
                        <p>
                            Proteína {plan.proteina_g.toFixed(0)} g · Grasa{" "}
                            {plan.grasa_g.toFixed(0)} g · Carbohidratos{" "}
                            {plan.carbohidratos_g.toFixed(0)} g
                        </p>
                    </div>
                    <div className="panel__acciones">
                        <Link className="panel__cta" to="/nuevo-plan">
                            Nuevo plan
                        </Link>
                        <Link className="panel__enlace" to="/calendario">
                            Registrar hoy
                        </Link>
                        <Link className="panel__enlace" to="/plan/como-se-calculo">
                            Cómo se calculó
                        </Link>
                    </div>
                </article>
            )}

            <div className="panel__pasos">
                <article>
                    <strong>1</strong>
                    <h3>Completa tu perfil</h3>
                    <p>
                        Revisa tu altura, actividad y nivel de entrenamiento.
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
                        Anota cada día tus calorías, tu peso y tu actividad
                        física en el calendario.
                    </p>
                    <Link to="/calendario">Ir al calendario</Link>
                </article>
            </div>
        </section>
    );
}
