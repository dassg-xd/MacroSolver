import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { mensajeDeError } from "../../api/mensajeError";
import {
    BloqueEsqueleto,
    EstadoEsqueleto,
    EsqueletoTabla,
} from "../../components/Esqueleto";
import EstadoPantalla from "../../components/EstadoPantalla";
import type { PlanHistorial } from "../../types/seguimiento";
import { conSigno, fechaCorta, num } from "../calendario/fechas";
import { obtenerHistorial } from "../seguimiento/seguimientoService";
import "../../styles/Pagina.css";
import "../../styles/Historial.css";

type Carga = { tipo: "ok"; planes: PlanHistorial[] } | { tipo: "error"; mensaje: string };

function anio(fecha: string): string {
    return fecha.slice(0, 4);
}

export default function Historial() {
    const [carga, setCarga] = useState<Carga | null>(null);
    const [intento, setIntento] = useState(0);

    useEffect(() => {
        let vigente = true;
        obtenerHistorial()
            .then((planes) => {
                if (vigente) setCarga({ tipo: "ok", planes });
            })
            .catch((error: unknown) => {
                if (vigente) setCarga({ tipo: "error", mensaje: mensajeDeError(error) });
            });
        return () => {
            vigente = false;
        };
    }, [intento]);

    return (
        <section className="pagina" aria-busy={carga === null}>
            <header className="pagina__cabecera">
                <div>
                    <h1>Historial de planes</h1>
                    <p>Cada re-planeación crea un plan nuevo encadenado al anterior. Ninguno se borra.</p>
                </div>
                <Link className="boton boton--primario pagina__accion" to="/nuevo-plan">
                    Nuevo plan
                </Link>
            </header>

            {carga === null && (
                <EstadoEsqueleto
                    mensaje="Cargando tus planes..."
                    className="historial__carga"
                >
                    {Array.from({ length: 3 }, (_, indice) => (
                        <article className="esqueleto__tarjeta" key={indice}>
                            <BloqueEsqueleto className="esqueleto__subtitulo" />
                            <BloqueEsqueleto className="esqueleto__linea" />
                            <EsqueletoTabla filas={2} />
                        </article>
                    ))}
                </EstadoEsqueleto>
            )}

            {carga?.tipo === "error" && (
                <EstadoPantalla
                    tipo="error"
                    titulo="No pudimos cargar el historial"
                    accion={
                        <button
                            type="button"
                            className="boton boton--secundario"
                            onClick={() => {
                                setCarga(null);
                                setIntento((actual) => actual + 1);
                            }}
                        >
                            Reintentar
                        </button>
                    }
                >
                    <p>{carga.mensaje}</p>
                </EstadoPantalla>
            )}

            {carga?.tipo === "ok" && carga.planes.length === 0 && (
                <EstadoPantalla
                    tipo="vacio"
                    titulo="Todavía no has creado ningún plan"
                    accion={
                        <Link className="boton boton--primario" to="/nuevo-plan">
                            Crear mi plan
                        </Link>
                    }
                >
                    <p>Cuando crees tu primer plan aparecerá aquí.</p>
                </EstadoPantalla>
            )}

            {carga?.tipo === "ok" && carga.planes.length > 0 && (
                <ol className="historial">
                    {carga.planes.map((plan, indice) => {
                        const activo = plan.estado === "activo";
                        const numero = carga.planes.length - indice;
                        return (
                            <li
                                key={plan.id}
                                className={`tarjeta historial__plan${activo ? " historial__plan--activo" : ""}`}
                                aria-current={activo ? "true" : undefined}
                            >
                                <header>
                                    <h2>Plan {numero}</h2>
                                    <span className={`etiqueta${activo ? " etiqueta--activo" : ""}`}>
                                        {activo ? "Activo" : "Anterior"}
                                    </span>
                                </header>
                                <p>
                                    {fechaCorta(plan.fecha_inicio)} de {anio(plan.fecha_inicio)} →{" "}
                                    {fechaCorta(plan.fecha_meta)} de {anio(plan.fecha_meta)}
                                    {plan.plan_previo_id !== null && " · reemplazó al plan anterior"}
                                </p>
                                <dl className="historial__datos">
                                    <div>
                                        <dt>Peso</dt>
                                        <dd>
                                            {num(plan.peso_inicial_kg)} → {num(plan.peso_objetivo_kg)} kg
                                        </dd>
                                    </div>
                                    <div>
                                        <dt>Ingesta</dt>
                                        <dd>{num(plan.ingesta_kcal, 0)} kcal/día</dd>
                                    </div>
                                    <div>
                                        <dt>Plazo</dt>
                                        <dd>{plan.plazo_dias} días</dd>
                                    </div>
                                    <div>
                                        <dt>Resultado</dt>
                                        <dd>
                                            {plan.ultimo_peso_kg !== null && plan.cambio_kg !== null
                                                ? `${num(plan.ultimo_peso_kg)} kg (${conSigno(plan.cambio_kg)} kg)`
                                                : "Sin pesos registrados"}
                                        </dd>
                                    </div>
                                </dl>
                                {activo && (
                                    <div className="historial__enlaces">
                                        <Link to="/panel">Ver en el panel</Link>
                                        <Link to="/plan/como-se-calculo">Cómo se calculó</Link>
                                    </div>
                                )}
                            </li>
                        );
                    })}
                </ol>
            )}
        </section>
    );
}
