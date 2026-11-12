import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    Legend,
    ResponsiveContainer,
    CartesianGrid,
} from "recharts";

import type { CalculoPlan, CurvaPlan } from "../../types/plan";

interface Props {
    calculo: CalculoPlan | null;
    curva?: CurvaPlan | null;
}

export default function ComoSeCalculo({ calculo, curva }: Props) {
    if (!calculo) {
        return (
            <p className="como__vacio">
                Todavía no hay datos de cálculo para mostrar.
            </p>
        );
    }

    const datos = curva
        ? curva.peso_kg.map((peso, indice) => ({
              dia: curva.dias[indice],
              peso,
              bandaInferior: curva.banda_inferior_kg[indice],
              bandaSuperior: curva.banda_superior_kg[indice],
          }))
        : [];
    const metodoComposicion =
        calculo.composicion.metodo === "marina"
            ? "circunferencias (fórmula de la Marina de EE. UU.)"
            : "IMC, edad y sexo (fórmula de Deurenberg)";

    return (
        <section className="como">
            <header className="como__cabecera">
                <h2>Cómo se calculó tu plan</h2>
                <p>
                    Estos son los pasos numéricos que llevan de tus datos a la
                    ingesta diaria y a la curva estimada.
                </p>
            </header>

            <article className="como__bloque">
                <h3>1. Composición inicial</h3>
                <p>
                    La estimación usa {metodoComposicion}. Resultado:{" "}
                    <strong>{calculo.composicion.pct_grasa.toFixed(1)} %</strong>{" "}
                    de grasa y{" "}
                    <strong>
                        {calculo.composicion.masa_libre_inicial_kg.toFixed(1)} kg
                    </strong>{" "}
                    de masa libre.
                </p>
                <p className="como__nota">
                    Es una estimación y no una medición directa de la composición corporal.
                </p>
            </article>

            <article className="como__bloque">
                <h3>2. Viabilidad</h3>
                <p>{calculo.viabilidad.mensaje}</p>
                <p>
                    Ingesta más rápida permitida:{" "}
                    <strong>
                        {calculo.viabilidad.ingesta_rapida_kcal.toFixed(0)} kcal
                    </strong>
                    . Días mínimos:{" "}
                    <strong>
                        {calculo.viabilidad.n_min_dias ?? "no alcanzable"}
                    </strong>
                    .
                </p>
            </article>

            <article className="como__bloque">
                <h3>3. Secante sobre Euler</h3>
                <p>
                    La Secante busca la ingesta que deja el peso del día{" "}
                    {calculo.secante.iteraciones.length > 0 ? "N" : ""} en la
                    meta, con tolerancia de {calculo.secante.tolerancia_kg} kg y
                    máximo {calculo.secante.max_iteraciones} iteraciones. Raíz
                    encontrada:{" "}
                    <strong>{calculo.secante.raiz_kcal.toFixed(0)} kcal</strong>{" "}
                    (error {calculo.secante.error_raiz_kg.toFixed(4)} kg).
                </p>
                <div className="como__tabla">
                    <table>
                        <thead>
                            <tr>
                                <th>n</th>
                                <th>Ingesta (kcal)</th>
                                <th>f(x) (kg)</th>
                                <th>Paso</th>
                            </tr>
                        </thead>
                        <tbody>
                            {calculo.secante.iteraciones.map((paso) => (
                                <tr key={paso.k}>
                                    <td>{paso.k}</td>
                                    <td>{paso.ingesta_kcal.toFixed(1)}</td>
                                    <td>{paso.error_kg.toFixed(4)}</td>
                                    <td>{paso.paso}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </article>

            <article className="como__bloque">
                <h3>4. Error de Euler frente a Runge-Kutta 4</h3>
                <p>
                    Euler explícito con paso de 1 día frente a RK4 con paso de 0,05
                    días. Error final:{" "}
                    <strong>{calculo.euler.error_final_kg.toFixed(4)} kg</strong>;
                    error máximo:{" "}
                    <strong>{calculo.euler.error_maximo_kg.toFixed(4)} kg</strong>.
                </p>
            </article>

            {curva && datos.length > 0 && (
                <article className="como__bloque">
                    <h3>5. Curva ideal y banda de tolerancia</h3>
                    <p>
                        El peso estimado va de {curva.peso_kg[0].toFixed(1)} kg a{" "}
                        {curva.peso_kg[curva.peso_kg.length - 1].toFixed(1)} kg.
                        Las líneas superior e inferior muestran la banda de tolerancia.
                    </p>
                    <div className="como__grafica">
                        <div
                            role="img"
                            aria-label={`Curva ideal: ${curva.peso_kg[0].toFixed(1)} kg al inicio y ${curva.peso_kg[curva.peso_kg.length - 1].toFixed(1)} kg al final, con bandas de tolerancia.`}
                        >
                            <ResponsiveContainer width="100%" height={290}>
                            <LineChart data={datos} margin={{ top: 10, right: 12, bottom: 20, left: 8 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    dataKey="dia"
                                    type="number"
                                    tickLine={false}
                                    label={{
                                        value: "Día del plan",
                                        position: "insideBottom",
                                        offset: -12,
                                    }}
                                />
                                <YAxis unit=" kg" width={58} />
                                <Tooltip
                                    formatter={(valor, nombre) => [
                                        `${Number(valor).toFixed(2)} kg`,
                                        nombre,
                                    ]}
                                    labelFormatter={(dia) => `Día ${dia}`}
                                />
                                <Legend wrapperStyle={{ fontSize: 11 }} />
                                <Line
                                    type="monotone"
                                    dataKey="bandaSuperior"
                                    stroke="#e0d8d1"
                                    strokeDasharray="4 3"
                                    dot={false}
                                    name="Banda superior"
                                    isAnimationActive={false}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="peso"
                                    stroke="#c91e27"
                                    strokeWidth={2}
                                    dot={false}
                                    name="Peso ideal"
                                    isAnimationActive={false}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="bandaInferior"
                                    stroke="#e0d8d1"
                                    strokeDasharray="4 3"
                                    dot={false}
                                    name="Banda inferior"
                                    isAnimationActive={false}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                        </div>
                    </div>
                </article>
            )}

            {calculo.sensibilidad && (
                <article className="como__bloque">
                    <h3>6. Sensibilidad de la ingesta</h3>
                    <p>
                        Variando el factor de actividad ±10 % y el porcentaje de
                        grasa ±3 puntos, la ingesta se mueve entre{" "}
                        <strong>
                            {calculo.sensibilidad.minimo_kcal.toFixed(0)}
                        </strong>{" "}
                        y{" "}
                        <strong>
                            {calculo.sensibilidad.maximo_kcal.toFixed(0)}
                        </strong>{" "}
                        kcal.
                    </p>
                </article>
            )}

            <details className="como__formulas">
                <summary>Ver fórmulas utilizadas</summary>
                <dl>
                    <div>
                        <dt>Modelo</dt>
                        <dd>{calculo.formulas.modelo}</dd>
                    </div>
                    <div>
                        <dt>Gasto energético</dt>
                        <dd>{calculo.formulas.tdee}</dd>
                    </div>
                    <div>
                        <dt>Simulación de peso</dt>
                        <dd>{calculo.formulas.euler}</dd>
                    </div>
                    <div>
                        <dt>Búsqueda de ingesta</dt>
                        <dd>{calculo.formulas.secante}</dd>
                    </div>
                    <div>
                        <dt>Reparto de macros</dt>
                        <dd>{calculo.formulas.macros}</dd>
                    </div>
                </dl>
            </details>

        </section>
    );
}
