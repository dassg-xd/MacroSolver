import {
    CartesianGrid,
    ComposedChart,
    Legend,
    Line,
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

/** Curva ideal, curva por adherencia, pesos reales y tendencia en un solo eje. */
export default function GraficaSeguimiento({ seguimiento: s }: Props) {
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
            className="grafica-seguimiento"
            role="img"
            aria-label="Gráfica de seguimiento del peso. Eje horizontal: día del plan. Eje vertical: peso en kilogramos."
        >
            <ResponsiveContainer width="100%" height={320}>
                <ComposedChart data={datos} margin={{ top: 10, right: 16, bottom: 20, left: 0 }}>
                    <CartesianGrid stroke="#efebe6" vertical={false} />
                    <XAxis
                        dataKey="dia"
                        type="number"
                        domain={[0, s.plazo_dias]}
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
                    <Tooltip
                        formatter={(valor, nombre, elemento) => [
                            `${num(Number(valor), 2)} kg`,
                            nombre === "Por adherencia" && elemento.payload.estimado
                                ? "Por adherencia (estimado)"
                                : nombre,
                        ]}
                        labelFormatter={(dia) => `Día ${dia}`}
                        contentStyle={{ fontSize: "var(--texto-secundario)", borderRadius: 8, borderColor: "#e6e1db" }}
                    />
                    <Legend wrapperStyle={{ fontSize: "var(--texto-secundario)", paddingTop: 8 }} iconSize={10} />
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
