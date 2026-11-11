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

const GLOSARIO: [string, string][] = [
    ["Ingesta del plan", "Las calorías diarias con las que el modelo llega a tu peso meta en la fecha elegida."],
    ["Curva ideal", "El peso que tendrías cada día si comieras exactamente la ingesta del plan."],
    ["Curva por adherencia", "El peso simulado con las calorías que sí registraste. Los días sin registro se simulan con la ingesta del plan y se marcan como estimados."],
    ["Tendencia", "Una curva ajustada a tus pesos reales que suaviza las subidas y bajadas del día a día."],
    ["Llegada estimada", "El día en que la curva por adherencia alcanza tu meta si sigues como vas."],
    ["Re-planeación", "Si tu tendencia se aleja más de 1 kg del plan, la app propone un plan nuevo desde tu peso real. Solo cambia si lo aceptas."],
    ["Día cumplido", "Un día cuyas calorías quedaron dentro de ±10 % de la ingesta del plan."],
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

    const guia = carga?.tipo === "ok" ? carga.guia : null;

    return (
        <section className="pagina">
            <header className="pagina__cabecera">
                <div>
                    <h1>Guía de nutrición</h1>
                    <p>Tus macros del plan activo, repartidos en el número de comidas que prefieras.</p>
                </div>
            </header>

            {carga === null && <p className="pagina__estado">Cargando la guía...</p>}

            {carga?.tipo === "error" && (
                <p className="pagina__error" role="alert">
                    {carga.mensaje}
                </p>
            )}

            {carga?.tipo === "sin-plan" && (
                <article className="tarjeta tarjeta--vacia">
                    <h2>Todavía no tienes un plan activo</h2>
                    <p>El reparto por comidas se calcula con los macros de tu plan.</p>
                    <Link className="boton boton--primario pagina__accion" to="/nuevo-plan">
                        Crear mi plan
                    </Link>
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
                        <div className="guia__encabezado">
                            <h2>Reparto por comidas</h2>
                            <div className="guia__opciones" role="radiogroup" aria-label="Número de comidas">
                                {OPCIONES.map((n) => (
                                    <button
                                        key={n}
                                        type="button"
                                        role="radio"
                                        aria-checked={comidas === n}
                                        className={comidas === n ? "activo" : ""}
                                        onClick={() => setComidas(n)}
                                    >
                                        {n} comidas
                                    </button>
                                ))}
                            </div>
                        </div>
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
                <dl className="guia__glosario">
                    {GLOSARIO.map(([termino, definicion]) => (
                        <div key={termino}>
                            <dt>{termino}</dt>
                            <dd>{definicion}</dd>
                        </div>
                    ))}
                </dl>
                <p className="tarjeta__nota guia__nota">
                    Esta guía aplica reglas generales y no reemplaza la asesoría de un profesional
                    de la salud.
                </p>
            </article>
        </section>
    );
}
