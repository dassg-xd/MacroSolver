import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import { mensajeDeError } from "../../api/mensajeError";
import type { Estadisticas as DatosEstadisticas, SemanaEstadistica } from "../../types/seguimiento";
import { conSigno, fechaBreve, num } from "../calendario/fechas";
import { esSinPlan, obtenerEstadisticas } from "../seguimiento/seguimientoService";
import "../../styles/Pagina.css";
import "../../styles/Estadisticas.css";

type Carga =
    | { tipo: "ok"; datos: DatosEstadisticas }
    | { tipo: "sin-plan" }
    | { tipo: "error"; mensaje: string };

function etiquetaSemana(s: SemanaEstadistica): string {
    return `${fechaBreve(s.inicio)} – ${fechaBreve(s.fin)}${s.parcial ? "*" : ""}`;
}

export default function Estadisticas() {
    const [carga, setCarga] = useState<Carga | null>(null);

    useEffect(() => {
        let vigente = true;
        obtenerEstadisticas()
            .then((datos) => {
                if (vigente) setCarga({ tipo: "ok", datos });
            })
            .catch((error: unknown) => {
                if (!vigente) return;
                setCarga(
                    esSinPlan(error)
                        ? { tipo: "sin-plan" }
                        : { tipo: "error", mensaje: mensajeDeError(error) },
                );
            });
        return () => {
            vigente = false;
        };
    }, []);

    return (
        <section className="pagina">
            <header className="pagina__cabecera">
                <div>
                    <h1>Estadísticas semanales</h1>
                    <p>Semanas de domingo a sábado. La semana en curso es parcial.</p>
                </div>
            </header>

            {carga === null && <p className="pagina__estado">Cargando estadísticas...</p>}

            {carga?.tipo === "error" && (
                <p className="pagina__error" role="alert">
                    {carga.mensaje}
                </p>
            )}

            {carga?.tipo === "sin-plan" && (
                <article className="tarjeta tarjeta--vacia">
                    <h2>Todavía no tienes un plan activo</h2>
                    <p>Las estadísticas se calculan con los registros de tu plan.</p>
                    <Link className="boton boton--primario pagina__accion" to="/nuevo-plan">
                        Crear mi plan
                    </Link>
                </article>
            )}

            {carga?.tipo === "ok" && <Contenido datos={carga.datos} />}
        </section>
    );
}

function Contenido({ datos }: { datos: DatosEstadisticas }) {
    const r = datos.resumen;
    const pct = Math.round(datos.banda_cumplimiento * 100);
    const semanas = datos.semanas;
    const conVariacion = semanas.filter((s) => s.variacion_kg !== null);
    const ritmo =
        conVariacion.length > 0
            ? conVariacion.reduce((suma, s) => suma + (s.variacion_kg ?? 0), 0) / conVariacion.length
            : null;
    const sesionesSemana = semanas.length > 0 ? r.sesiones / semanas.length : 0;
    const barras = semanas
        .filter((s) => s.adherencia_pct !== null)
        .map((s) => ({
        semana: etiquetaSemana(s),
        adherencia: s.adherencia_pct ?? undefined,
        detalle: `${s.dias_cumplidos} de ${s.dias_registrados}`,
        parcial: s.parcial,
        }));
    const variaciones = semanas
        .filter((s) => s.variacion_kg !== null)
        .map((s) => ({
            semana: etiquetaSemana(s),
            variacion: s.variacion_kg ?? undefined,
            parcial: s.parcial,
        }));

    return (
        <>
            <div className="kpis">
                <article className="kpi">
                    <span className="kpi__etiqueta">Adherencia acumulada</span>
                    <span className="kpi__valor">
                        {r.dias_cumplidos} de {r.dias_registrados}
                    </span>
                    <span className="kpi__detalle">
                        días registrados dentro de ±{pct} %
                        {r.adherencia_pct !== null && ` (${num(r.adherencia_pct, 0)} %)`}
                    </span>
                </article>
                <article className="kpi">
                    <span className="kpi__etiqueta">Promedio de calorías</span>
                    <span className="kpi__valor">
                        {r.promedio_kcal !== null ? num(r.promedio_kcal, 0) : "—"}
                        <small>kcal</small>
                    </span>
                    <span className="kpi__detalle">Objetivo: {num(r.objetivo_kcal, 0)} kcal</span>
                </article>
                <article className="kpi">
                    <span className="kpi__etiqueta">Cambio de peso</span>
                    <span className="kpi__valor">
                        {conSigno(r.cambio_kg)}
                        <small>kg</small>
                    </span>
                    <span className="kpi__detalle">
                        {ritmo !== null
                            ? `Ritmo promedio: ${conSigno(ritmo, 2)} kg/semana`
                            : `De ${num(r.peso_inicial_kg)} a ${num(r.peso_actual_kg)} kg`}
                    </span>
                </article>
                <article className="kpi">
                    <span className="kpi__etiqueta">Entrenamiento</span>
                    <span className="kpi__valor">
                        {num(sesionesSemana)}
                        <small>sesiones/semana</small>
                    </span>
                    <span className="kpi__detalle">
                        {r.sesiones} sesiones · {r.minutos} min en total
                    </span>
                </article>
            </div>

            <article className="tarjeta">
                <h2>Adherencia por semana</h2>
                <p>
                    Porcentaje de días registrados que quedaron dentro de ±{pct} % de la ingesta.
                    El denominador excluye los días sin registro.
                </p>
                {barras.length === 0 ? (
                    <p className="tarjeta__nota">
                        Aún no hay semanas con calorías registradas. Anótalas en el{" "}
                        <Link to="/calendario">calendario</Link>; las semanas sin datos no se
                        representan como 0 %.
                    </p>
                ) : (
                    <div
                        className="estadisticas__grafica"
                        role="img"
                        aria-label={`Adherencia semanal calculada sobre días registrados. ${barras.length} semanas con datos.`}
                    >
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={barras} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
                                <CartesianGrid stroke="#efebe6" vertical={false} />
                                <XAxis
                                    dataKey="semana"
                                    tick={{ fontSize: 12, fill: "#77737a" }}
                                    tickLine={false}
                                    axisLine={{ stroke: "#dcd7d1" }}
                                />
                                <YAxis
                                    domain={[0, 100]}
                                    ticks={[0, 50, 100]}
                                    unit=" %"
                                    tick={{ fontSize: 12, fill: "#77737a" }}
                                    tickLine={false}
                                    axisLine={false}
                                    width={56}
                                />
                                <Tooltip
                                    formatter={(valor, _nombre, item) => [
                                        `${num(Number(valor), 0)} % (${item.payload.detalle} días)`,
                                        "Adherencia",
                                    ]}
                                    contentStyle={{ fontSize: 14, borderRadius: 8, borderColor: "#e6e1db" }}
                                    cursor={{ fill: "#f7f5f2" }}
                                />
                                <Bar dataKey="adherencia" radius={[5, 5, 0, 0]} maxBarSize={56} isAnimationActive={false}>
                                    {barras.map((b) => (
                                        <Cell key={b.semana} fill={b.parcial ? "#e9a3a6" : "#e0242b"} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                )}
                <p className="tarjeta__nota">
                    * Semana en curso, parcial. La tabla conserva el detalle y muestra “—” cuando
                    no hay denominador o peso medido.
                </p>
            </article>

            <article className="tarjeta">
                <h2>Variación semanal del peso</h2>
                <p>
                    Cambio entre promedios de peso de semanas consecutivas, en kg. Debajo de cero
                    indica descenso; por encima, aumento. El dato procede de la respuesta del plan.
                </p>
                {variaciones.length === 0 ? (
                    <p className="tarjeta__nota">
                        Aún no hay pesos de semanas consecutivas para mostrar una variación.
                    </p>
                ) : (
                    <>
                        <div
                            className="estadisticas__grafica estadisticas__grafica--variacion"
                            role="img"
                            aria-label={`Variación de peso en ${variaciones.length} semanas con observaciones. Los valores negativos indican descenso y los positivos aumento.`}
                        >
                            <ResponsiveContainer width="100%" height={220}>
                                <BarChart
                                    data={variaciones}
                                    margin={{ top: 8, right: 8, bottom: 0, left: -18 }}
                                >
                                    <CartesianGrid stroke="#efebe6" vertical={false} />
                                    <XAxis
                                        dataKey="semana"
                                        tick={{ fontSize: 12, fill: "#77737a" }}
                                        tickLine={false}
                                        axisLine={{ stroke: "#dcd7d1" }}
                                    />
                                    <YAxis
                                        unit=" kg"
                                        tick={{ fontSize: 12, fill: "#77737a" }}
                                        tickLine={false}
                                        axisLine={false}
                                        width={58}
                                    />
                                    <ReferenceLine y={0} stroke="#77737a" />
                                    <Tooltip
                                        formatter={(valor) => [
                                            `${conSigno(Number(valor), 2)} kg`,
                                            "Variación semanal",
                                        ]}
                                        contentStyle={{
                                            fontSize: 14,
                                            borderRadius: 8,
                                            borderColor: "#e6e1db",
                                        }}
                                    />
                                    <Bar
                                        dataKey="variacion"
                                        name="Variación semanal"
                                        radius={[5, 5, 0, 0]}
                                        maxBarSize={56}
                                        isAnimationActive={false}
                                    >
                                        {variaciones.map((semana) => (
                                            <Cell
                                                key={semana.semana}
                                                fill={
                                                    (semana.variacion ?? 0) <= 0
                                                        ? "#1c6b3a"
                                                        : "#b8700c"
                                                }
                                            />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                        <p className="tarjeta__nota">
                            Se grafica solo cuando existe una variación; las semanas sin peso
                            permanecen como “—” en la tabla.
                        </p>
                    </>
                )}
            </article>

            <article className="tarjeta">
                <h2>Detalle por semana</h2>
                <div className="tabla-contenedor">
                    <table className="tabla">
                        <thead>
                            <tr>
                                <th>Semana</th>
                                <th>Peso promedio</th>
                                <th>Variación</th>
                                <th>Adherencia</th>
                                <th>Sesiones</th>
                                <th>Minutos</th>
                                <th>kcal por ejercicio (aprox.)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {[...semanas].reverse().map((s) => (
                                <tr key={s.inicio}>
                                    <td>
                                        {fechaBreve(s.inicio)} – {fechaBreve(s.fin)}
                                        {s.parcial && " · en curso"}
                                    </td>
                                    <td>{s.peso_promedio_kg !== null ? `${num(s.peso_promedio_kg, 2)} kg` : "—"}</td>
                                    <td>{s.variacion_kg !== null ? conSigno(s.variacion_kg, 2) : "—"}</td>
                                    <td>
                                        {s.dias_registrados > 0
                                            ? `${s.dias_cumplidos} de ${s.dias_registrados}`
                                            : "—"}
                                    </td>
                                    <td>{s.sesiones}</td>
                                    <td>{s.minutos}</td>
                                    <td>{s.kcal_ejercicio > 0 ? `≈ ${num(s.kcal_ejercicio, 0)}` : "—"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </article>
        </>
    );
}
