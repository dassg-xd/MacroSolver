import { isAxiosError } from "axios";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Link } from "react-router-dom";

import { mensajeDeError } from "../../api/mensajeError";
import type { ActividadCatalogo, Calendario as DatosCalendario, DiaCalendario } from "../../types/registro";
import {
    BloqueEsqueleto,
    EstadoEsqueleto,
} from "../../components/Esqueleto";
import EstadoPantalla from "../../components/EstadoPantalla";
import "../../styles/Calendario.css";
import {
    INICIALES_DIA,
    diaSemana,
    formatoKcal,
    hoyLocal,
    mesDe,
    moverMes,
    numeroDia,
    tituloDia,
    tituloMes,
} from "./fechas";
import PanelDia, { type ResultadoGuardado } from "./PanelDia";
import { obtenerCalendario, obtenerCatalogoActividades } from "./registroService";

type CargaCatalogo =
    | { tipo: "cargando" }
    | { tipo: "ok"; actividades: ActividadCatalogo[] }
    | { tipo: "error"; mensaje: string };

type Carga =
    | { clave: string; tipo: "ok"; datos: DatosCalendario }
    | { clave: string; tipo: "sin-plan" }
    | { clave: string; tipo: "error"; mensaje: string };

function seleccionable(dia: DiaCalendario): boolean {
    return dia.estado === "registrado" || dia.estado === "estimado";
}

function claseDia(dia: DiaCalendario, hoy: string, seleccionado: boolean): string {
    const clases = ["calendario__dia", `calendario__dia--${dia.estado.replaceAll("_", "-")}`];
    if (dia.fecha === hoy) clases.push("calendario__dia--hoy");
    if (dia.cumplido === true) clases.push("calendario__dia--cumplido");
    if (dia.cumplido === false) clases.push("calendario__dia--desviado");
    if (seleccionado) clases.push("calendario__dia--seleccionado");
    return clases.join(" ");
}

function etiquetaEstadoDia(dia: DiaCalendario): string {
    if (dia.estado === "registrado") {
        if (dia.cumplido === true) return "Cumplido";
        if (dia.cumplido === false) return "Desviado";
        return "Registrado";
    }
    if (dia.estado === "estimado") return "Estimado";
    if (dia.estado === "futuro") return "Futuro";
    return "Fuera plan";
}

export default function Calendario() {
    const hoy = hoyLocal();
    const [mes, setMes] = useState(mesDe(hoy));
    const [version, setVersion] = useState(0);
    const [carga, setCarga] = useState<Carga | null>(null);
    const [cargaCatalogo, setCargaCatalogo] = useState<CargaCatalogo>({
        tipo: "cargando",
    });
    const [versionCatalogo, setVersionCatalogo] = useState(0);
    const [seleccion, setSeleccion] = useState<string | null>(null);
    const [resultadoGuardado, setResultadoGuardado] =
        useState<ResultadoGuardado | null>(null);
    const referenciasDias = useRef(new Map<string, HTMLButtonElement>());

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
        let vigente = true;
        obtenerCatalogoActividades()
            .then((actividades) => {
                if (vigente) {
                    setCargaCatalogo({ tipo: "ok", actividades });
                }
            })
            .catch((error: unknown) => {
                if (vigente) {
                    setCargaCatalogo({
                        tipo: "error",
                        mensaje: mensajeDeError(error),
                    });
                }
            });

        return () => {
            vigente = false;
        };
    }, [versionCatalogo]);

    const cargando = carga?.clave !== clave;
    // Mientras llega el mes nuevo se sigue mostrando el anterior, atenuado.
    const datos = carga?.tipo === "ok" ? carga.datos : null;
    const catalogo =
        cargaCatalogo.tipo === "ok" ? cargaCatalogo.actividades : [];

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
    const primerDiaSeleccionable = datos?.dias.find(seleccionable)?.fecha ?? null;
    const fechaEnTab = diaSeleccionado?.fecha ?? primerDiaSeleccionable;

    function moverSeleccionConTeclado(
        evento: KeyboardEvent<HTMLButtonElement>,
        dia: DiaCalendario,
    ) {
        if (!datos) return;

        const indice = datos.dias.findIndex((actual) => actual.fecha === dia.fecha);
        if (indice < 0) return;

        let destino: number | null = null;
        if (evento.key === "ArrowLeft") destino = indice - 1;
        if (evento.key === "ArrowRight") destino = indice + 1;
        if (evento.key === "ArrowUp") destino = indice - 7;
        if (evento.key === "ArrowDown") destino = indice + 7;
        if (evento.key === "Home") {
            destino = Math.max(0, indice - ((huecos + indice) % 7));
        }
        if (evento.key === "End") {
            destino = Math.min(
                datos.dias.length - 1,
                indice + (6 - ((huecos + indice) % 7)),
            );
        }
        if (destino === null) return;

        evento.preventDefault();
        let paso = destino < indice ? -1 : 1;
        if (evento.key === "ArrowUp") paso = -7;
        if (evento.key === "ArrowDown") paso = 7;
        if (evento.key === "Home") paso = 1;
        if (evento.key === "End") paso = -1;
        while (
            destino >= 0 &&
            destino < datos.dias.length &&
            !seleccionable(datos.dias[destino])
        ) {
            destino += paso;
        }
        const siguiente = datos.dias[destino];
        if (!siguiente || !seleccionable(siguiente)) return;

        setResultadoGuardado(null);
        setSeleccion(siguiente.fecha);
        referenciasDias.current.get(siguiente.fecha)?.focus();
    }

    return (
        <section
            className="calendario"
            aria-busy={cargando}
        >
            <Cabecera />

            {cargaCatalogo.tipo === "error" && (
                <EstadoPantalla
                    tipo="error"
                    titulo="No pudimos cargar las actividades"
                    accion={
                        <button
                            className="boton boton--secundario"
                            type="button"
                            onClick={() => {
                                setCargaCatalogo({ tipo: "cargando" });
                                setVersionCatalogo((actual) => actual + 1);
                            }}
                        >
                            Reintentar
                        </button>
                    }
                >
                    <p>{cargaCatalogo.mensaje}</p>
                    <p>Puedes seguir registrando calorías y peso.</p>
                </EstadoPantalla>
            )}
            {cargaCatalogo.tipo === "ok" &&
                cargaCatalogo.actividades.length === 0 && (
                    <p className="calendario__cargando" role="status">
                        No hay actividades disponibles. Puedes seguir registrando
                        calorías y peso.
                    </p>
                )}

            {carga?.tipo === "error" && (
                <p className="calendario__error" role="alert">
                    {carga.mensaje}
                </p>
            )}

            {resultadoGuardado &&
                resultadoGuardado.fecha === diaSeleccionado?.fecha && (
                    <p
                        className={
                            resultadoGuardado.tipo === "parcial"
                                ? "calendario__error"
                                : "calendario__guardado"
                        }
                        role={resultadoGuardado.tipo === "parcial" ? "alert" : "status"}
                    >
                        {resultadoGuardado.tipo === "completo"
                            ? "Cambios del día guardados."
                            : `Se guardaron ${resultadoGuardado.guardadas} de ${resultadoGuardado.guardadas + resultadoGuardado.fallidas} actualizaciones. Estamos actualizando el calendario. ${resultadoGuardado.mensaje}`}
                    </p>
                )}

            <div className="calendario__cuerpo">
                <article className={`calendario__mes${cargando && datos ? " calendario__mes--cargando" : ""}`}>
                    <header className="calendario__navegacion">
                        <button
                            type="button"
                            className="calendario__flecha"
                            aria-label="Mes anterior"
                            disabled={!mesMinimo || mes <= mesMinimo}
                            onClick={() => {
                                setResultadoGuardado(null);
                                setMes(moverMes(mes, -1));
                            }}
                        >
                            ‹
                        </button>
                        <h2>{tituloMes(mes)}</h2>
                        <button
                            type="button"
                            className="calendario__flecha"
                            aria-label="Mes siguiente"
                            disabled={!mesMaximo || mes >= mesMaximo}
                            onClick={() => {
                                setResultadoGuardado(null);
                                setMes(moverMes(mes, 1));
                            }}
                        >
                            ›
                        </button>
                    </header>

                    <div className="calendario__semana" aria-hidden="true">
                        {INICIALES_DIA.map((d) => (
                            <span key={d}>{d}</span>
                        ))}
                    </div>

                    {!datos && cargando && (
                        <EstadoEsqueleto
                            mensaje="Cargando el mes..."
                            className="calendario__carga-mes"
                        >
                            <div className="esqueleto__calendario">
                                {Array.from({ length: 35 }, (_, indice) => (
                                    <BloqueEsqueleto
                                        className="esqueleto__dia"
                                        key={indice}
                                    />
                                ))}
                            </div>
                        </EstadoEsqueleto>
                    )}

                    {datos && (
                        <div
                            className="calendario__cuadricula"
                            role="group"
                            aria-label={`Días de ${tituloMes(mes)}. Usa las flechas para cambiar de día.`}
                        >
                            {Array.from({ length: huecos }, (_, i) => (
                                <span
                                    key={`hueco-${i}`}
                                    className="calendario__hueco"
                                    aria-hidden="true"
                                />
                            ))}
                            {datos.dias.map((dia) => {
                                const activo = seleccionable(dia);
                                const elegido = diaSeleccionado?.fecha === dia.fecha;
                                return (
                                    <button
                                        key={dia.fecha}
                                        type="button"
                                        className={claseDia(dia, hoy, elegido)}
                                        disabled={!activo}
                                        tabIndex={
                                            activo && dia.fecha === fechaEnTab ? 0 : -1
                                        }
                                        aria-pressed={elegido}
                                        aria-current={dia.fecha === hoy ? "date" : undefined}
                                        aria-label={`${tituloDia(dia.fecha)}, ${etiquetaEstadoDia(dia)}${elegido ? ", seleccionado" : ""}${
                                            dia.kcal !== null
                                                ? `, ${formatoKcal(dia.kcal)} kcal`
                                                : ""
                                        }`}
                                        ref={(elemento) => {
                                            if (elemento) {
                                                referenciasDias.current.set(dia.fecha, elemento);
                                            } else {
                                                referenciasDias.current.delete(dia.fecha);
                                            }
                                        }}
                                        onKeyDown={(evento) =>
                                            moverSeleccionConTeclado(evento, dia)
                                        }
                                        onClick={() => {
                                            setResultadoGuardado(null);
                                            setSeleccion(dia.fecha);
                                        }}
                                    >
                                        <span className="calendario__numero">{numeroDia(dia.fecha)}</span>
                                        {dia.fecha === hoy && <span className="calendario__hoy">HOY</span>}
                                        <span className="calendario__estado">
                                            {etiquetaEstadoDia(dia)}
                                        </span>
                                        {elegido && (
                                            <span className="calendario__seleccionado">
                                                Seleccionado
                                            </span>
                                        )}
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
                        cargandoCatalogo={cargaCatalogo.tipo === "cargando"}
                        onGuardado={(resultado) => {
                            setResultadoGuardado(resultado);
                            setVersion((actual) => actual + 1);
                        }}
                    />
                )}

                {datos && !diaSeleccionado && (
                    <aside className="dia dia--vacio">
                        <p>Elige un día del plan, hasta hoy, para ver o editar su registro.</p>
                    </aside>
                )}

                {!datos && cargando && (
                    <aside className="dia calendario__panel-esqueleto" aria-hidden="true">
                        <BloqueEsqueleto className="esqueleto__subtitulo" />
                        <BloqueEsqueleto className="esqueleto__linea" />
                        <BloqueEsqueleto className="esqueleto__campo" />
                        <BloqueEsqueleto className="esqueleto__campo" />
                        <BloqueEsqueleto className="esqueleto__boton" />
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
