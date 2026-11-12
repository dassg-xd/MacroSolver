import { useRef, useState } from "react";
import { RotateCcw } from "lucide-react";
import {
    CartesianGrid,
    ComposedChart,
    Legend,
    Line,
    ReferenceArea,
    ReferenceLine,
    ResponsiveContainer,
    Scatter,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import type { Seguimiento } from "../../types/seguimiento";
import { num } from "../calendario/fechas";

interface Props {
    seguimiento: Seguimiento;
}

const COLORES = {
    ideal: "#171719",
    adherencia: "#e0242b",
    tendencia: "#2f6fb5",
    real: "#1c6b3a",
};

interface SeleccionRango {
    inicio: number;
    fin: number;
}

function diaActivo(etiqueta: string | number | undefined): number | null {
    if (etiqueta === undefined) return null;
    const dia = Number(etiqueta);
    return Number.isFinite(dia) ? dia : null;
}

/** Curva ideal, curva por adherencia, pesos reales y tendencia en un solo eje. */
export default function GraficaSeguimiento({ seguimiento: s }: Props) {
    const [rangoZoom, setRangoZoom] = useState<[number, number] | null>(null);
    const [seleccion, setSeleccion] = useState<SeleccionRango | null>(null);
    const [arrastrando, setArrastrando] = useState(false);
    const inicioSeleccion = useRef<number | null>(null);

    function iniciarSeleccion(etiqueta: string | number | undefined) {
        const dia = diaActivo(etiqueta);
        if (dia === null) return;
        inicioSeleccion.current = dia;
        setSeleccion({ inicio: dia, fin: dia });
        setArrastrando(true);
    }

    function actualizarSeleccion(etiqueta: string | number | undefined) {
        const inicio = inicioSeleccion.current;
        if (inicio === null) return;
        const dia = diaActivo(etiqueta);
        if (dia === null) return;
        setSeleccion((actual) =>
            actual?.fin === dia
                ? actual
                : { inicio, fin: dia },
        );
    }

    function cancelarSeleccion() {
        inicioSeleccion.current = null;
        setSeleccion(null);
        setArrastrando(false);
    }

    function finalizarSeleccion(etiqueta: string | number | undefined) {
        const inicio = inicioSeleccion.current;
        const fin = diaActivo(etiqueta) ?? seleccion?.fin ?? inicio;

        if (inicio !== null && fin !== null && Math.abs(fin - inicio) >= 2) {
            const desde = Math.max(0, Math.min(inicio, fin));
            const hasta = Math.min(s.plazo_dias, Math.max(inicio, fin));
            setRangoZoom([desde, hasta]);
        }

        inicioSeleccion.current = null;
        setSeleccion(null);
        setArrastrando(false);
    }

    const reales = new Map(s.pesos.map((p) => [p.dia, p.peso_kg]));
    const datos = s.dias.map((dia) => ({
        dia,
        ideal: s.curva_ideal[dia],
        adherencia: s.curva_adherencia[dia],
        estimado: s.estimado[dia] ?? false,
        adherenciaEstimada: s.estimado[dia]
            ? s.curva_adherencia[dia]
            : undefined,
        tendencia: s.tendencia ? s.tendencia.curva[dia] : undefined,
        real: reales.get(dia),
    }));

    const valores = datos.flatMap((d) =>
        [d.ideal, d.adherencia, d.real, s.peso_objetivo_kg].filter(
            (v): v is number => typeof v === "number",
        ),
    );
    const minimo = Math.floor(Math.min(...valores) - 1);
    const maximo = Math.ceil(Math.max(...valores) + 1);
    const paso = maximo - minimo > 10 ? 2 : 1;
    const marcas: number[] = [];
    for (let v = minimo; v <= maximo; v += paso) marcas.push(v);

    return (
        <div
            className={`grafica-seguimiento${arrastrando ? " grafica-seguimiento--seleccionando" : ""}`}
            role="group"
            aria-label="Gráfica interactiva de seguimiento del peso."
        >
            <div className="grafica-seguimiento__controles">
                <span>
                    Arrastra sobre la gráfica para ampliar un rango de días.
                </span>
                {rangoZoom && (
                    <button
                        type="button"
                        className="boton boton--secundario"
                        onClick={() => setRangoZoom(null)}
                    >
                        <RotateCcw size={16} aria-hidden="true" />
                        Restablecer zoom
                    </button>
                )}
            </div>
            <ResponsiveContainer width="100%" height={340}>
                <ComposedChart
                    data={datos}
                    margin={{ top: 10, right: 16, bottom: 36, left: 0 }}
                    onMouseDown={(estado) => iniciarSeleccion(estado.activeLabel)}
                    onMouseMove={(estado) => actualizarSeleccion(estado.activeLabel)}
                    onMouseUp={(estado) => finalizarSeleccion(estado.activeLabel)}
                    onMouseLeave={cancelarSeleccion}
                >
                    <CartesianGrid stroke="#efebe6" vertical={false} />
                    <XAxis
                        dataKey="dia"
                        type="number"
                        domain={rangoZoom ?? [0, s.plazo_dias]}
                        allowDataOverflow={rangoZoom !== null}
                        tickCount={7}
                        tick={{ fontSize: "var(--texto-eje-marca)", fill: "#77737a" }}
                        tickLine={false}
                        axisLine={{ stroke: "#dcd7d1" }}
                        label={{
                            value: "Día del plan",
                            position: "insideBottom",
                            offset: -10,
                            fontSize: "var(--texto-eje-titulo)",
                            fill: "#5d5960",
                        }}
                    />
                    <YAxis
                        domain={[minimo, maximo]}
                        ticks={marcas}
                        tick={{ fontSize: "var(--texto-eje-marca)", fill: "#77737a" }}
                        tickLine={false}
                        axisLine={false}
                        unit=" kg"
                        width={70}
                        label={{
                            value: "Peso (kg)",
                            angle: -90,
                            position: "insideLeft",
                            fontSize: "var(--texto-eje-titulo)",
                            fill: "#5d5960",
                        }}
                    />
                    {arrastrando && seleccion && seleccion.inicio !== seleccion.fin && (
                        <ReferenceArea
                            x1={Math.min(seleccion.inicio, seleccion.fin)}
                            x2={Math.max(seleccion.inicio, seleccion.fin)}
                            y1={maximo}
                            y2={minimo}
                            fill="#c41e24"
                            fillOpacity={0.14}
                            stroke="#c41e24"
                            strokeOpacity={0.5}
                        />
                    )}
                    <Tooltip
                        formatter={(valor, nombre, elemento) => [
                            `${num(Number(valor), 2)} kg`,
                            nombre === "Por adherencia" && elemento.payload.estimado
                                ? "Por adherencia (estimado)"
                                : nombre,
                        ]}
                        labelFormatter={(dia) => `Día ${dia}`}
                        contentStyle={{ fontSize: "var(--texto-secundario)", borderRadius: 8, borderColor: "#e6e1db"}}
                    />
                    <Legend wrapperStyle={{ fontSize: "var(--texto-secundario)", paddingTop: 28 }} position={"bottom"}  iconSize={10} />
                    <ReferenceLine
                        y={s.peso_objetivo_kg}
                        stroke="#b3afb4"
                        strokeDasharray="4 4"
                        label={{
                            value: `Meta ${num(s.peso_objetivo_kg)} kg`,
                            position: "insideBottomLeft",
                            fontSize: "var(--texto-etiqueta)",
                            fill: "#77737a",
                        }}
                    />
                    <ReferenceLine
                        x={s.dia_actual}
                        stroke="#b3afb4"
                        label={{ value: "Hoy", position: "insideTopRight", fontSize: "var(--texto-etiqueta)", fill: "#77737a" }}
                    />
                    <Line
                        name="Curva ideal"
                        dataKey="ideal"
                        stroke={COLORES.ideal}
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                    />
                    <Line
                        name="Por adherencia"
                        dataKey="adherencia"
                        stroke={COLORES.adherencia}
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                    />
                    <Scatter
                        name="Días estimados"
                        dataKey="adherenciaEstimada"
                        fill={COLORES.adherencia}
                        shape="square"
                        legendType="square"
                        isAnimationActive={false}
                    />
                    {s.tendencia && (
                        <Line
                            name="Tendencia"
                            dataKey="tendencia"
                            stroke={COLORES.tendencia}
                            strokeWidth={1.5}
                            strokeDasharray="6 4"
                            dot={false}
                            isAnimationActive={false}
                        />
                    )}
                    <Line
                        name="Pesos reales"
                        dataKey="real"
                        stroke={COLORES.real}
                        strokeWidth={0}
                        dot={{ r: 4, fill: COLORES.real, stroke: "#fff", strokeWidth: 1.5 }}
                        activeDot={{ r: 5 }}
                        legendType="circle"
                        isAnimationActive={false}
                    />
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
}
