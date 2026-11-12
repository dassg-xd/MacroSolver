import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { mensajeDeError } from "../../api/mensajeError";
import type { Guia as DatosGuia } from "../../types/seguimiento";
import { num } from "../calendario/fechas";
import { esSinPlan, obtenerGuia } from "../seguimiento/seguimientoService";
import "../../styles/Pagina.css";
import "../../styles/Guia.css";

type Carga =
    | { comidas: number; tipo: "ok"; guia: DatosGuia }
    | { comidas: number; tipo: "sin-plan" }
    | { comidas: number; tipo: "error"; mensaje: string };

const OPCIONES = [3, 4, 5];

const GLOSARIO = [
    {
        id: "glosario-plan",
        titulo: "Plan y meta",
        terminos: [
            ["Ingesta del plan", "Calorías diarias que el modelo estima para alcanzar tu meta en la fecha elegida."],
            ["Curva ideal", "Peso estimado cada día si consumes exactamente las calorías del plan."],
        ],
    },
    {
        id: "glosario-progreso",
        titulo: "Tu progreso",
        terminos: [
            ["Curva por adherencia", "Peso simulado con las calorías que registraste. Los días sin registro usan la ingesta del plan y se marcan como estimados."],
            ["Tendencia", "Curva de tus pesos registrados que suaviza las subidas y bajadas del día a día."],
            ["Llegada estimada", "Día en que la curva por adherencia alcanza tu meta si mantienes el ritmo actual."],
        ],
    },
    {
        id: "glosario-ajustes",
        titulo: "Cumplimiento y ajustes",
        terminos: [
            ["Día cumplido", "Día en que tus calorías quedaron dentro de ±10 % de la ingesta del plan."],
            ["Re-planeación", "Si tu tendencia se desvía más de 1 kg del plan, se propone un plan nuevo desde tu peso real. Solo cambia si lo aceptas."],
        ],
    },
];

export default function Guia() {
    const [comidas, setComidas] = useState(4);
    const [carga, setCarga] = useState<Carga | null>(null);

    useEffect(() => {
        let vigente = true;
        obtenerGuia(comidas)
            .then((guia) => {
                if (vigente) setCarga({ comidas, tipo: "ok", guia });
            })
            .catch((error: unknown) => {
                if (!vigente) return;
                setCarga(
                    esSinPlan(error)
                        ? { comidas, tipo: "sin-plan" }
                        : { comidas, tipo: "error", mensaje: mensajeDeError(error) },
                );
            });
        return () => {
            vigente = false;
        };
    }, [comidas]);

    const cargaActual = carga?.comidas === comidas ? carga : null;
    const guia = cargaActual?.tipo === "ok" ? cargaActual.guia : null;

    return (
        <section className="pagina" aria-busy={cargaActual === null}>
            <header className="pagina__cabecera">
                <div>
                    <h1>Guía de nutrición</h1>
                    <p>Tus macros del plan activo, repartidos en el número de comidas que prefieras.</p>
                </div>
            </header>

            {cargaActual === null && (
                <p className="guia__estado" role="status">
                    Actualizando la guía para {comidas} comidas...
                </p>
            )}

            {cargaActual?.tipo === "error" && (
                <p className="pagina__error" role="alert">
                    {cargaActual.mensaje}
                </p>
            )}

            {cargaActual?.tipo === "sin-plan" && (
                <article className="tarjeta tarjeta--vacia">
                    <h2>Todavía no tienes un plan activo</h2>
                    <p>El reparto por comidas se calcula con los macros de tu plan.</p>
                    <Link className="boton boton--primario pagina__accion" to="/nuevo-plan">
                        Crear mi plan
                    </Link>
                </article>
            )}

            {cargaActual?.tipo !== "sin-plan" && (
                <article className="tarjeta">
                    <div className="guia__encabezado">
                        <div>
                            <h2>Repartir en</h2>
                            <p>Elige cuántas comidas haces al día.</p>
                        </div>
                        <div
                            className="guia__opciones"
                            role="group"
                            aria-label="Número de comidas"
                        >
                            {OPCIONES.map((n) => (
                                <button
                                    key={n}
                                    type="button"
                                    aria-pressed={comidas === n}
                                    className={comidas === n ? "activo" : ""}
                                    onClick={() => setComidas(n)}
                                >
                                    {n} comidas
                                </button>
                            ))}
                        </div>
                    </div>
                </article>
            )}

            {guia && (
                <>
                    <div className="kpis">
                        <article className="kpi">
                            <span className="kpi__etiqueta">Energía</span>
                            <span className="kpi__valor">
                                {num(guia.ingesta_kcal, 0)}
                                <small>kcal</small>
                            </span>
                            <span className="kpi__detalle">Ingesta diaria del plan</span>
                        </article>
                        <article className="kpi">
                            <span className="kpi__etiqueta">Proteína</span>
                            <span className="kpi__valor">
                                {num(guia.proteina_g, 0)}
                                <small>g</small>
                            </span>
                            <span className="kpi__detalle">2,2 g por kg de masa libre</span>
                        </article>
                        <article className="kpi">
                            <span className="kpi__etiqueta">Grasa</span>
                            <span className="kpi__valor">
                                {num(guia.grasa_g, 0)}
                                <small>g</small>
                            </span>
                            <span className="kpi__detalle">25 % de la energía</span>
                        </article>
                        <article className="kpi">
                            <span className="kpi__etiqueta">Carbohidratos</span>
                            <span className="kpi__valor">
                                {num(guia.carbohidratos_g, 0)}
                                <small>g</small>
                            </span>
                            <span className="kpi__detalle">El resto de la energía</span>
                        </article>
                    </div>

                    <article className="tarjeta">
                        <h2>Reparto por comidas</h2>
                        <p>
                            Reparto para {guia.comidas} comidas · {num(guia.ingesta_kcal, 0)} kcal al día.
                        </p>
                        <div className="tabla-contenedor">
                            <table className="tabla">
                                <thead>
                                    <tr>
                                        <th>Comida</th>
                                        <th>Parte del día</th>
                                        <th>Energía</th>
                                        <th>Proteína</th>
                                        <th>Grasa</th>
                                        <th>Carbohidratos</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {guia.reparto.map((c) => (
                                        <tr key={c.nombre}>
                                            <td>
                                                <strong>{c.nombre}</strong>
                                            </td>
                                            <td>{c.porcentaje} %</td>
                                            <td>{num(c.kcal, 0)} kcal</td>
                                            <td>{num(c.proteina_g, 0)} g</td>
                                            <td>{num(c.grasa_g, 0)} g</td>
                                            <td>{num(c.carbohidratos_g, 0)} g</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        <p className="tarjeta__nota guia__nota">
                            El reparto sigue reglas fijas: la comida principal concentra más energía
                            y la proteína se distribuye en todas las comidas.
                        </p>
                    </article>

                    <article className="tarjeta">
                        <h2>Consejos para cumplir el plan</h2>
                        <ul className="guia__consejos">
                            {guia.consejos.map((c) => (
                                <li key={c}>{c}</li>
                            ))}
                        </ul>
                    </article>
                </>
            )}

            <article className="tarjeta">
                <h2>Qué significa cada número</h2>
                <div className="guia__glosario">
                    {GLOSARIO.map(({ id, titulo, terminos }) => (
                        <section
                            className="guia__glosario-grupo"
                            aria-labelledby={id}
                            key={id}
                        >
                            <h3 id={id}>{titulo}</h3>
                            <dl>
                                {terminos.map(([termino, definicion]) => (
                                    <div key={termino}>
                                        <dt>{termino}</dt>
                                        <dd>{definicion}</dd>
                                    </div>
                                ))}
                            </dl>
                        </section>
                    ))}
                </div>
                <p className="tarjeta__nota guia__nota">
                    Esta guía aplica reglas generales y no reemplaza la asesoría de un profesional
                    de la salud.
                </p>
            </article>
        </section>
    );
}
