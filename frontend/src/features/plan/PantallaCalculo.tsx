import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { obtenerCalculoActivo, obtenerPlanActivo } from "../plan/planService";
import type { CalculoPlan, PlanActivo } from "../../types/plan";
import ComoSeCalculo from "../plan/ComoSeCalculo";
import "../../styles/ComoSeCalculo.css";

export default function PantallaCalculo() {
    const [calculo, setCalculo] = useState<CalculoPlan | null>(null);
    const [plan, setPlan] = useState<PlanActivo | null>(null);
    const [cargando, setCargando] = useState(true);

    useEffect(() => {
        Promise.all([obtenerCalculoActivo(), obtenerPlanActivo()])
            .then(([c, p]) => {
                setCalculo(c);
                setPlan(p);
            })
            .finally(() => setCargando(false));
    }, []);

    return (
        <section className="como-pantalla">
            <header className="como-pantalla__cabecera">
                <Link className="como-pantalla__volver" to="/panel">
                    ← Volver al panel
                </Link>
                <h1>Cómo se calculó mi plan</h1>
                {plan && (
                    <p>
                        Plan del {plan.fecha_inicio} al {plan.fecha_meta} ·{" "}
                        {plan.ingesta_kcal.toFixed(0)} kcal/día
                    </p>
                )}
            </header>

            {cargando && <p>Cargando el cálculo...</p>}
            {!cargando && !calculo && (
                <p>
                    Todavía no tienes un plan activo.{" "}
                    <Link to="/nuevo-plan">Crea uno</Link>.
                </p>
            )}
            {!cargando && calculo && (
                <ComoSeCalculo calculo={calculo} />
            )}
        </section>
    );
}
