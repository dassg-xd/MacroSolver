import { useState } from "react";

import { mensajeDeError } from "../../api/mensajeError";
import type { ActividadCatalogo, ActividadDia, DiaCalendario } from "../../types/registro";
import { formatoKcal, tituloDia } from "./fechas";
import { guardarActividades, guardarCalorias, guardarPeso } from "./registroService";

interface Props {
    dia: DiaCalendario;
    ingestaObjetivo: number;
    banda: number;
    esDiaInicial: boolean;
    catalogo: ActividadCatalogo[];
    onGuardado: () => void;
}

function aTexto(valor: number | null): string {
    return valor === null ? "" : String(valor);
}

/** "1 950" o "79,4" → número; vacío → null; texto inválido → NaN. */
function aNumero(texto: string): number | null {
    const limpio = texto.trim().replace(/\s/g, "").replace(",", ".");
    if (limpio === "") return null;
    return Number(limpio);
}

function mismasActividades(a: ActividadDia[], b: ActividadDia[]): boolean {
    return (
        a.length === b.length &&
        a.every((x, i) => x.actividad_id === b[i].actividad_id && x.minutos === b[i].minutos)
    );
}

export default function PanelDia({ dia, ingestaObjetivo, banda, esDiaInicial, catalogo, onGuardado }: Props) {
    const originales: ActividadDia[] = dia.actividades.map((a) => ({
        actividad_id: a.actividad_id,
        minutos: a.minutos,
    }));

    const [kcal, setKcal] = useState(aTexto(dia.kcal));
    const [peso, setPeso] = useState(aTexto(dia.peso_kg));
    const [actividades, setActividades] = useState<ActividadDia[]>(originales);
    const [nuevaActividad, setNuevaActividad] = useState("");
    const [nuevosMinutos, setNuevosMinutos] = useState("30");
    const [guardando, setGuardando] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const nombre = (id: number) => catalogo.find((a) => a.id === id);
    const pct = Math.round(banda * 100);
    const detalle =
        dia.estado === "registrado" ? "registrado" : "sin registro: se simula con el plan";

    function agregarActividad() {
        const id = Number(nuevaActividad || catalogo[0]?.id);
        const minutos = Number(nuevosMinutos);
        if (!id) return;
        if (!Number.isInteger(minutos) || minutos < 1 || minutos > 600) {
            setError("Los minutos deben ser un número entero entre 1 y 600.");
            return;
        }
        setError(null);
        setActividades((lista) => [...lista, { actividad_id: id, minutos }]);
    }

    async function guardarDia() {
        const valorKcal = aNumero(kcal);
        const valorPeso = aNumero(peso);
        if (valorKcal !== null && (Number.isNaN(valorKcal) || valorKcal < 0 || valorKcal > 10000)) {
            setError("Las calorías deben ser un número entre 0 y 10 000.");
            return;
        }
        if (valorPeso !== null && (Number.isNaN(valorPeso) || valorPeso < 30 || valorPeso > 300)) {
            setError("El peso debe estar entre 30 y 300 kg.");
            return;
        }

        const pendientes: Promise<unknown>[] = [];
        if (valorKcal !== dia.kcal) pendientes.push(guardarCalorias(dia.fecha, valorKcal));
        if (!esDiaInicial && valorPeso !== dia.peso_kg) pendientes.push(guardarPeso(dia.fecha, valorPeso));
        if (!mismasActividades(actividades, originales)) {
            pendientes.push(guardarActividades(dia.fecha, actividades));
        }
        if (pendientes.length === 0) {
            setError("No hay cambios para guardar.");
            return;
        }

        setGuardando(true);
        setError(null);
        const resultados = await Promise.allSettled(pendientes);
        setGuardando(false);
        const fallo = resultados.find((r): r is PromiseRejectedResult => r.status === "rejected");
        if (fallo) {
            setError(mensajeDeError(fallo.reason));
            return;
        }
        onGuardado();
    }

    return (
        <aside className="dia" aria-labelledby="titulo-dia">
            <header className="dia__cabecera">
                <h2 id="titulo-dia">{tituloDia(dia.fecha)}</h2>
                <p>
                    Día {dia.dia_plan} del plan · {detalle}
                </p>
            </header>

            <div className="dia__campos">
                <label className="dia__campo">
                    <span>Calorías (kcal)</span>
                    <input
                        inputMode="numeric"
                        value={kcal}
                        placeholder="Ej. 1950"
                        onChange={(e) => setKcal(e.target.value)}
                    />
                </label>
                <label className="dia__campo">
                    <span>Peso (kg)</span>
                    <input
                        inputMode="decimal"
                        value={peso}
                        placeholder={esDiaInicial ? "" : "Opcional"}
                        disabled={esDiaInicial}
                        onChange={(e) => setPeso(e.target.value)}
                    />
                </label>
            </div>
            <p className="dia__nota">
                Objetivo del día: {formatoKcal(ingestaObjetivo)} kcal (±{pct} % cuenta como cumplido).
                {esDiaInicial && " El peso del día de inicio es el peso inicial del plan."}
            </p>

            <h3 className="dia__subtitulo">Actividad física</h3>
            {actividades.length === 0 ? (
                <p className="dia__nota">Sin actividades: cuenta como descanso.</p>
            ) : (
                <ul className="dia__actividades">
                    {actividades.map((a, i) => {
                        const info = nombre(a.actividad_id);
                        const registrada = dia.actividades.find(
                            (r) => r.actividad_id === a.actividad_id && r.minutos === a.minutos,
                        );
                        return (
                            <li key={`${a.actividad_id}-${i}`}>
                                <div>
                                    <strong>{info?.nombre ?? "Actividad"}</strong>
                                    <span>
                                        {a.minutos} min
                                        {registrada && ` · ≈ ${formatoKcal(registrada.kcal_estimadas)} kcal aprox.`}
                                    </span>
                                </div>
                                <button
                                    type="button"
                                    className="dia__quitar"
                                    aria-label={`Quitar ${info?.nombre ?? "actividad"}`}
                                    onClick={() => setActividades((lista) => lista.filter((_, j) => j !== i))}
                                >
                                    ×
                                </button>
                            </li>
                        );
                    })}
                </ul>
            )}

            <div className="dia__agregar">
                <label className="dia__campo">
                    <span>Actividad</span>
                    <select value={nuevaActividad} onChange={(e) => setNuevaActividad(e.target.value)}>
                        {catalogo.map((a) => (
                            <option key={a.id} value={a.id}>
                                {a.nombre} · {a.tipo === "fuerza" ? "fuerza" : "aeróbico"}
                            </option>
                        ))}
                    </select>
                </label>
                <label className="dia__campo dia__campo--corto">
                    <span>Minutos</span>
                    <input
                        inputMode="numeric"
                        value={nuevosMinutos}
                        onChange={(e) => setNuevosMinutos(e.target.value)}
                    />
                </label>
            </div>
            <button
                type="button"
                className="dia__boton-agregar"
                disabled={catalogo.length === 0}
                onClick={agregarActividad}
            >
                + Agregar actividad
            </button>

            {error && (
                <p className="dia__error" role="alert">
                    {error}
                </p>
            )}

            <button
                type="button"
                className="boton boton--primario dia__guardar"
                disabled={guardando}
                onClick={guardarDia}
            >
                {guardando ? "Guardando..." : "Guardar día"}
            </button>
            <p className="dia__pie">
                El gasto por ejercicio es una estimación aproximada (MET). Al guardar,
                el panel se recalcula.
            </p>
        </aside>
    );
}
