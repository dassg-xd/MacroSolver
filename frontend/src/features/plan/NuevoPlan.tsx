import { useState, type SubmitEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useSesion } from "../auth/SesionContext";
import { vistaPreviaPlan, confirmarPlan } from "./planService";
import type { VistaPreviaPlan, DatosPlan } from "../../types/plan";
import ComoSeCalculo from "./ComoSeCalculo";
import "../../styles/NuevoPlan.css";

export default function NuevoPlan() {
    const { usuario } = useSesion();
    const navegar = useNavigate();

    const [pesoInicial, setPesoInicial] = useState("");
    const [pesoMeta, setPesoMeta] = useState("");
    const [fechaInicio, setFechaInicio] = useState(
        new Date().toISOString().slice(0, 10)
    );
    const [fechaMeta, setFechaMeta] = useState("");
    const [cuello, setCuello] = useState("");
    const [cintura, setCintura] = useState("");
    const [cadera, setCadera] = useState("");

    const [previa, setPrevia] = useState<VistaPreviaPlan | null>(null);
    const [cargando, setCargando] = useState(false);
    const [confirmando, setConfirmando] = useState(false);
    const [error, setError] = useState("");

    const esMujer = usuario?.sexo === "Femenino";

    async function enviar(event: SubmitEvent<HTMLFormElement>) {
        event.preventDefault();
        setError("");
        setCargando(true);
        try {
            const datos: DatosPlan = {
                peso_inicial_kg: Number(pesoInicial),
                peso_objetivo_kg: Number(pesoMeta),
                fecha_inicio: fechaInicio,
                fecha_meta: fechaMeta,
                cuello_cm: cuello ? Number(cuello) : undefined,
                cintura_cm: cintura ? Number(cintura) : undefined,
                cadera_cm: esMujer && cadera ? Number(cadera) : undefined,
            };
            const resultado = await vistaPreviaPlan(datos);
            setPrevia(resultado);
        } catch {
            setError("No se pudo calcular la vista previa. Revisa los datos.");
        } finally {
            setCargando(false);
        }
    }

    async function confirmar() {
        if (!previa?.puede_confirmar) return;
        setConfirmando(true);
        setError("");
        try {
            const datos: DatosPlan = {
                peso_inicial_kg: Number(pesoInicial),
                peso_objetivo_kg: Number(pesoMeta),
                fecha_inicio: fechaInicio,
                fecha_meta: fechaMeta,
                cuello_cm: cuello ? Number(cuello) : undefined,
                cintura_cm: cintura ? Number(cintura) : undefined,
                cadera_cm: esMujer && cadera ? Number(cadera) : undefined,
            };
            await confirmarPlan(datos);
            navegar("/panel", { replace: true });
        } catch {
            setError("No se pudo guardar el plan. Intenta de nuevo.");
        } finally {
            setConfirmando(false);
        }
    }

    return (
        <section className="nuevo-plan">
            <header className="nuevo-plan__cabecera">
                <h1>Nuevo plan</h1>
                <p>
                    Define tu meta y las medidas. Antes de confirmar verás la
                    ingesta, los macros, la curva y los bloqueos de seguridad.
                </p>
            </header>

            <form className="nuevo-plan__formulario" onSubmit={enviar}>
                <div className="nuevo-plan__grid">
                    <label>
                        Peso inicial (kg)
                        <input
                            type="number"
                            step="0.1"
                            value={pesoInicial}
                            onChange={(e) => setPesoInicial(e.target.value)}
                            required
                        />
                    </label>
                    <label>
                        Peso meta (kg)
                        <input
                            type="number"
                            step="0.1"
                            value={pesoMeta}
                            onChange={(e) => setPesoMeta(e.target.value)}
                            required
                        />
                    </label>
                    <label>
                        Fecha de inicio
                        <input
                            type="date"
                            value={fechaInicio}
                            onChange={(e) => setFechaInicio(e.target.value)}
                            required
                        />
                    </label>
                    <label>
                        Fecha meta
                        <input
                            type="date"
                            value={fechaMeta}
                            onChange={(e) => setFechaMeta(e.target.value)}
                            required
                        />
                    </label>
                    <label>
                        Cuello (cm)
                        <input
                            type="number"
                            step="0.1"
                            value={cuello}
                            onChange={(e) => setCuello(e.target.value)}
                        />
                    </label>
                    <label>
                        Cintura (cm)
                        <input
                            type="number"
                            step="0.1"
                            value={cintura}
                            onChange={(e) => setCintura(e.target.value)}
                        />
                    </label>
                    {esMujer && (
                        <label>
                            Cadera (cm)
                            <input
                                type="number"
                                step="0.1"
                                value={cadera}
                                onChange={(e) => setCadera(e.target.value)}
                            />
                        </label>
                    )}
                </div>

                <div className="nuevo-plan__acciones">
                    <button
                        type="submit"
                        className="boton boton--primario"
                        disabled={cargando}
                    >
                        {cargando ? "Calculando..." : "Calcular vista previa"}
                    </button>
                    <Link className="boton boton--secundario" to="/panel">
                        Volver al panel
                    </Link>
                </div>
            </form>

            {error && <p className="nuevo-plan__error" role="alert">{error}</p>}

            {previa && (
                <div className="nuevo-plan__resultado">
                    <section className="nuevo-plan__tarjeta">
                        <h2>Composición inicial</h2>
                        <p>
                            {previa.composicion.pct_grasa.toFixed(1)} % de grasa
                            ({previa.composicion.metodo}). Masa libre:{" "}
                            {previa.composicion.masa_libre_inicial_kg.toFixed(1)}{" "}
                            kg.
                        </p>
                    </section>

                    {previa.bloqueos.length > 0 && (
                        <section className="nuevo-plan__bloqueos">
                            <h2>Bloqueos</h2>
                            <ul>
                                {previa.bloqueos.map((b) => (
                                    <li key={b.codigo}>{b.mensaje}</li>
                                ))}
                            </ul>
                            {previa.viabilidad.fecha_viable && (
                                <p>
                                    Fecha viable:{" "}
                                    <strong>{previa.viabilidad.fecha_viable}</strong>
                                    {previa.viabilidad.ingesta_viable_kcal && (
                                        <>
                                            {" "}
                                            con{" "}
                                            <strong>
                                                {previa.viabilidad.ingesta_viable_kcal.toFixed(
                                                    0
                                                )}
                                                kcal
                                            </strong>
                                        </>
                                    )}
                                    .
                                </p>
                            )}
                        </section>
                    )}

                    {previa.advertencias.length > 0 && (
                        <section className="nuevo-plan__avisos">
                            <h2>Avisos</h2>
                            <ul>
                                {previa.advertencias.map((a, i) => (
                                    <li key={i}>{a}</li>
                                ))}
                            </ul>
                        </section>
                    )}

                    {previa.puede_confirmar && previa.ingesta_kcal && (
                        <>
                            <section className="nuevo-plan__tarjeta">
                                <h2>Ingesta diaria</h2>
                                <p className="nuevo-plan__ingesta">
                                    {previa.ingesta_kcal.toFixed(0)} kcal
                                </p>
                                {previa.macros && (
                                    <p>
                                        Proteína {previa.macros.proteina_g.toFixed(0)} g ·
                                        Grasa {previa.macros.grasa_g.toFixed(0)} g ·
                                        Carbohidratos{" "}
                                        {previa.macros.carbohidratos_g.toFixed(0)} g
                                    </p>
                                )}
                            </section>

                            {previa.perdida && (
                                <section className="nuevo-plan__tarjeta">
                                    <h2>Pérdida estimada</h2>
                                    <p>
                                        Peso {previa.perdida.peso_kg.toFixed(1)} kg ·
                                        Grasa {previa.perdida.grasa_kg.toFixed(1)} kg ·
                                        Masa libre{" "}
                                        {previa.perdida.masa_libre_kg.toFixed(1)} kg
                                    </p>
                                </section>
                            )}

                            <section className="nuevo-plan__grafica">
                                <h2>Curva ideal</h2>
                                {/* Recharts importado en ComoSeCalculo; aquí resumen textual */}
                                <p>
                                    El peso pasa de {previa.composicion.grasa_inicial_kg.toFixed(
                                        1
                                    )}{" "}
                                    kg de grasa inicial a la meta en{" "}
                                    {previa.plazo_dias} días, con una banda de
                                    tolerancia de 1 kg.
                                </p>
                            </section>

                            <ComoSeCalculo
                                calculo={previa.calculo}
                                curva={previa.curva}
                            />

                            <div className="nuevo-plan__confirmar">
                                <button
                                    type="button"
                                    className="boton boton--primario"
                                    disabled={confirmando}
                                    onClick={confirmar}
                                >
                                    {confirmando ? "Guardando..." : "Confirmar plan"}
                                </button>
                            </div>
                        </>
                    )}
                </div>
            )}
        </section>
    );
}
