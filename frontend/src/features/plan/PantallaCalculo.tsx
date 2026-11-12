import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Calculator, Plus, RefreshCw } from "lucide-react";

import {
    BloqueEsqueleto,
    EstadoEsqueleto,
} from "../../components/Esqueleto";
import EstadoPantalla from "../../components/EstadoPantalla";
import { mensajeDeError } from "../../api/mensajeError";
import { obtenerCalculoActivo, obtenerPlanActivo } from "../plan/planService";
import type { CalculoPlan, PlanActivo } from "../../types/plan";
import ComoSeCalculo from "../plan/ComoSeCalculo";
import "../../styles/ComoSeCalculo.css";

type Carga =
    | { tipo: "cargando" }
    | { tipo: "sin-plan" }
    | { tipo: "sin-calculo" }
    | { tipo: "error"; mensaje: string }
    | { tipo: "ok"; calculo: CalculoPlan; plan: PlanActivo };

export default function PantallaCalculo() {
    const [carga, setCarga] = useState<Carga>({ tipo: "cargando" });
    const [intento, setIntento] = useState(0);

    useEffect(() => {
        let vigente = true;

        Promise.all([obtenerCalculoActivo(), obtenerPlanActivo()])
            .then(([c, p]) => {
                if (!vigente) {
                    return;
                }
                if (!p) {
                    setCarga({ tipo: "sin-plan" });
                } else if (!c) {
                    setCarga({ tipo: "sin-calculo" });
                } else {
                    setCarga({ tipo: "ok", calculo: c, plan: p });
                }
            })
            .catch((error: unknown) => {
                if (vigente) {
                    setCarga({ tipo: "error", mensaje: mensajeDeError(error) });
                }
            });

        return () => {
            vigente = false;
        };
    }, [intento]);

    function reintentar() {
        setCarga({ tipo: "cargando" });
        setIntento((actual) => actual + 1);
    }

    return (
        <section className="como-pantalla" aria-busy={carga.tipo === "cargando"}>
            <header className="como-pantalla__cabecera">
                <Link className="como-pantalla__volver" to="/panel">
                    <ArrowLeft size={16} aria-hidden="true" />
                    Volver al panel
                </Link>
                <h1>
                    <Calculator className="icono-ui" size={21} aria-hidden="true" />
                    Cómo se calculó mi plan
                </h1>
                {carga.tipo === "ok" && (
                    <p>
                        Plan del {carga.plan.fecha_inicio} al {carga.plan.fecha_meta} ·{" "}
                        {carga.plan.ingesta_kcal.toFixed(0)} kcal/día
                    </p>
                )}
            </header>

            {carga.tipo === "cargando" && (
                <EstadoEsqueleto
                    mensaje="Cargando el cálculo..."
                    className="como__carga"
                >
                    {Array.from({ length: 3 }, (_, indice) => (
                        <article className="esqueleto__tarjeta" key={indice}>
                            <BloqueEsqueleto className="esqueleto__subtitulo" />
                            <BloqueEsqueleto className="esqueleto__linea" />
                            <BloqueEsqueleto className="esqueleto__linea esqueleto__linea--ancha" />
                        </article>
                    ))}
                    <article className="esqueleto__tarjeta">
                        <BloqueEsqueleto className="esqueleto__subtitulo" />
                        <BloqueEsqueleto className="esqueleto__grafica" />
                    </article>
                </EstadoEsqueleto>
            )}
            {carga.tipo === "sin-plan" && (
                <EstadoPantalla
                    tipo="vacio"
                    titulo="Todavía no tienes un plan activo"
                    accion={
                        <Link className="boton boton--primario" to="/nuevo-plan">
                            <Plus size={17} aria-hidden="true" />
                            Crear un plan
                        </Link>
                    }
                >
                    <p>Cuando crees un plan podrás consultar cómo se calculó.</p>
                </EstadoPantalla>
            )}
            {carga.tipo === "sin-calculo" && (
                <EstadoPantalla
                    tipo="error"
                    titulo="No encontramos el cálculo de tu plan"
                    accion={
                        <button
                            className="boton boton--secundario"
                            type="button"
                            onClick={reintentar}
                        >
                            <RefreshCw size={16} aria-hidden="true" />
                            Reintentar
                        </button>
                    }
                >
                    <p>Tu plan está activo, pero no pudimos obtener su explicación.</p>
                </EstadoPantalla>
            )}
            {carga.tipo === "error" && (
                <EstadoPantalla
                    tipo="error"
                    titulo="No pudimos cargar el cálculo"
                    accion={
                        <button
                            className="boton boton--secundario"
                            type="button"
                            onClick={reintentar}
                        >
                            <RefreshCw size={16} aria-hidden="true" />
                            Reintentar
                        </button>
                    }
                >
                    <p>{carga.mensaje}</p>
                </EstadoPantalla>
            )}
            {carga.tipo === "ok" && (
                <ComoSeCalculo calculo={carga.calculo} />
            )}
        </section>
    );
}
