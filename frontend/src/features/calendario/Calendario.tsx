import { isAxiosError } from "axios";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { mensajeDeError } from "../../api/mensajeError";
import type { ActividadCatalogo, Calendario as DatosCalendario, DiaCalendario } from "../../types/registro";
import "../../styles/Calendario.css";
import {
    INICIALES_DIA,
    diaSemana,
    formatoKcal,
    hoyLocal,
    mesDe,
    moverMes,
    numeroDia,
    tituloMes,
} from "./fechas";
import PanelDia from "./PanelDia";
import { obtenerCalendario, obtenerCatalogoActividades } from "./registroService";

type Carga =
    | { clave: string; tipo: "ok"; datos: DatosCalendario }
    | { clave: string; tipo: "sin-plan" }
    | { clave: string; tipo: "error"; mensaje: string };

function seleccionable(dia: DiaCalendario): boolean {
    return dia.estado === "registrado" || dia.estado === "estimado";
}

function claseDia(dia: DiaCalendario, hoy: string, seleccionado: boolean): string {
    const clases = ["calendario__dia", `calendario__dia--${dia.estado.replace("_", "-")}`];
    if (dia.fecha === hoy) clases.push("calendario__dia--hoy");
    if (dia.cumplido === true) clases.push("calendario__dia--cumplido");
    if (dia.cumplido === false) clases.push("calendario__dia--desviado");
    if (seleccionado) clases.push("calendario__dia--seleccionado");
    return clases.join(" ");
}

export default function Calendario() {
    const hoy = hoyLocal();
    const [mes, setMes] = useState(mesDe(hoy));
    const [version, setVersion] = useState(0);
    const [carga, setCarga] = useState<Carga | null>(null);
    const [catalogo, setCatalogo] = useState<ActividadCatalogo[]>([]);
    const [seleccion, setSeleccion] = useState<string | null>(null);

    const clave = `${mes}#${version}`;

    useEffect(() => {
        let vigente = true;
        obtenerCalendario(mes)
            .then((datos) => {
                if (vigente) setCarga({ clave, tipo: "ok", datos });
            })
            .catch((error: unknown) => {
                if (!vigente) return;
                if (isAxiosError(error) && error.response?.status === 404) {
                    setCarga({ clave, tipo: "sin-plan" });
                } else {
                    setCarga({ clave, tipo: "error", mensaje: mensajeDeError(error) });
                }
            });
        return () => {
            vigente = false;
        };
    }, [mes, clave]);

    useEffect(() => {
        obtenerCatalogoActividades()
            .then(setCatalogo)
            .catch(() => setCatalogo([]));
    }, []);

    const cargando = carga?.clave !== clave;
    // Mientras llega el mes nuevo se sigue mostrando el anterior, atenuado.
    const datos = carga?.tipo === "ok" ? carga.datos : null;

    if (carga?.tipo === "sin-plan") {
        return (
            <section className="calendario">
                <Cabecera />
                <article className="calendario__vacio">
                    <h2>Todavía no tienes un plan activo</h2>
                    <p>
                        El calendario registra tus días dentro de un plan. Crea uno
                        para empezar a anotar calorías, peso y actividad física.
                    </p>
                    <Link className="boton boton--primario calendario__cta" to="/nuevo-plan">
                        Crear mi plan
                    </Link>
                </article>
            </section>
        );
    }

    const diaSeleccionado =
        datos?.dias.find((d) => d.fecha === seleccion && seleccionable(d)) ??
        datos?.dias.find((d) => d.fecha === hoy && seleccionable(d)) ??
        null;

    const mesMinimo = datos ? mesDe(datos.fecha_inicio) : null;
    const mesMaximo = datos ? mesDe(datos.fecha_meta < hoy ? datos.fecha_meta : hoy) : null;
    const huecos = datos && datos.dias.length > 0 ? diaSemana(datos.dias[0].fecha) : 0;

    return (
        <section className="calendario">
            <Cabecera />

            {carga?.tipo === "error" && (
                <p className="calendario__error" role="alert">
                    {carga.mensaje}
                </p>
            )}

            <div className="calendario__cuerpo">
                <article className={`calendario__mes${cargando ? " calendario__mes--cargando" : ""}`}>
                    <header className="calendario__navegacion">
                        <button
                            type="button"
                            className="calendario__flecha"
                            aria-label="Mes anterior"
                            disabled={!mesMinimo || mes <= mesMinimo}
                            onClick={() => setMes(moverMes(mes, -1))}
                        >
                            ‹
                        </button>
                        <h2>{tituloMes(mes)}</h2>
                        <button
                            type="button"
                            className="calendario__flecha"
                            aria-label="Mes siguiente"
                            disabled={!mesMaximo || mes >= mesMaximo}
                            onClick={() => setMes(moverMes(mes, 1))}
                        >
                            ›
                        </button>
                    </header>

                    <div className="calendario__semana" aria-hidden="true">
                        {INICIALES_DIA.map((d) => (
                            <span key={d}>{d}</span>
                        ))}
                    </div>

                    {!datos && cargando && <p className="calendario__cargando">Cargando el mes...</p>}

                    {datos && (
                        <div className="calendario__cuadricula" role="grid" aria-label={tituloMes(mes)}>
                            {Array.from({ length: huecos }, (_, i) => (
                                <span key={`hueco-${i}`} className="calendario__hueco" />
                            ))}
                            {datos.dias.map((dia) => {
                                const activo = seleccionable(dia);
                                const elegido = diaSeleccionado?.fecha === dia.fecha;
                                return (
                                    <button
                                        key={dia.fecha}
                                        type="button"
                                        role="gridcell"
                                        className={claseDia(dia, hoy, elegido)}
                                        disabled={!activo}
                                        aria-pressed={elegido}
                                        aria-label={`Día ${numeroDia(dia.fecha)}${
                                            dia.kcal !== null ? `, ${formatoKcal(dia.kcal)} kcal` : ""
                                        }`}
                                        onClick={() => setSeleccion(dia.fecha)}
                                    >
                                        <span className="calendario__numero">{numeroDia(dia.fecha)}</span>
                                        {dia.fecha === hoy && <span className="calendario__hoy">HOY</span>}
                                        {dia.kcal !== null && (
                                            <span className="calendario__kcal">{formatoKcal(dia.kcal)}</span>
                                        )}
                                        {dia.estado === "estimado" && (
                                            <span className="calendario__estimado">estimado</span>
                                        )}
                                        <span className="calendario__marcas" aria-hidden="true">
                                            {dia.peso_kg !== null && <i className="calendario__marca calendario__marca--peso" />}
                                            {dia.actividades.length > 0 && (
                                                <i className="calendario__marca calendario__marca--actividad" />
                                            )}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    )}

                    <ul className="calendario__leyenda">
                        <li><i className="calendario__muestra calendario__muestra--cumplido" />Calorías dentro de ±10 %</li>
                        <li><i className="calendario__muestra calendario__muestra--desviado" />Fuera de ±10 %</li>
                        <li><i className="calendario__marca calendario__marca--peso" />Peso</li>
                        <li><i className="calendario__marca calendario__marca--actividad" />Actividad</li>
                        <li><i className="calendario__muestra calendario__muestra--estimado" />Estimado con el plan</li>
                    </ul>
                </article>

                {datos && diaSeleccionado && (
                    <PanelDia
                        key={`${diaSeleccionado.fecha}#${version}`}
                        dia={diaSeleccionado}
                        ingestaObjetivo={datos.ingesta_objetivo_kcal}
                        banda={datos.banda_cumplimiento}
                        esDiaInicial={diaSeleccionado.fecha === datos.fecha_inicio}
                        catalogo={catalogo}
                        onGuardado={() => setVersion((v) => v + 1)}
                    />
                )}

                {datos && !diaSeleccionado && (
                    <aside className="dia dia--vacio">
                        <p>Elige un día del plan, hasta hoy, para ver o editar su registro.</p>
                    </aside>
                )}
            </div>
        </section>
    );
}

function Cabecera() {
    return (
        <header className="calendario__cabecera">
            <h1>Calendario</h1>
            <p>Toca un día para registrar calorías, peso y actividad física.</p>
        </header>
    );
}
