import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { mensajeDeError } from "../../api/mensajeError";
import EsqueletoPagina from "../../components/Esqueleto";
import { useSesion } from "../auth/SesionContext";
import { conSigno, fechaCorta, num, tituloDia } from "../calendario/fechas";
import { obtenerPlanActivo } from "../plan/planService";
import GraficaSeguimiento from "../seguimiento/GraficaSeguimiento";
import Replaneacion from "../seguimiento/Replaneacion";
import { esSinPlan, obtenerSeguimiento } from "../seguimiento/seguimientoService";
import type { PlanActivo } from "../../types/plan";
import type { Seguimiento } from "../../types/seguimiento";
import "../../styles/Pagina.css";
import "../../styles/Panel.css";

type Carga =
    | { version: number; tipo: "ok"; plan: PlanActivo; seguimiento: Seguimiento }
    | { version: number; tipo: "sin-plan" }
    | { version: number; tipo: "error"; mensaje: string };

export default function Panel() {
    const { usuario } = useSesion();
    const nombre = usuario?.nombre?.split(" ")[0] ?? "";
    const [version, setVersion] = useState(0);
    const [carga, setCarga] = useState<Carga | null>(null);
    const [replaneando, setReplaneando] = useState(false);

    useEffect(() => {
        let vigente = true;
        Promise.all([obtenerPlanActivo(), obtenerSeguimiento()])
            .then(([plan, seguimiento]) => {
                if (!vigente) return;
                setCarga(
                    plan
                        ? { version, tipo: "ok", plan, seguimiento }
                        : { version, tipo: "sin-plan" },
                );
            })
            .catch((error: unknown) => {
                if (!vigente) return;
                setCarga(
                    esSinPlan(error)
                        ? { version, tipo: "sin-plan" }
                        : { version, tipo: "error", mensaje: mensajeDeError(error) },
                );
            });
        return () => {
            vigente = false;
        };
    }, [version]);

    if (carga === null) {
        return <EsqueletoPagina tipo="panel" mensaje="Cargando tu plan..." />;
    }

    if (carga.tipo === "error") {
        return (
            <section className="pagina">
                <header className="pagina__cabecera">
                    <h1>Panel de seguimiento</h1>
                </header>
                <p className="pagina__error" role="alert">
                    {carga.mensaje}
                </p>
            </section>
        );
    }

    if (carga.tipo === "sin-plan") {
        return <PanelSinPlan nombre={nombre} />;
    }

    const { plan, seguimiento: s } = carga;
    const cambio = s.hoy.ultimo_peso_kg - plan.peso_inicial_kg;
    const retraso = s.llegada.retraso_dias;
    const diferenciaHoy = s.hoy.kcal !== null ? s.hoy.kcal - s.hoy.objetivo_kcal : null;
    const diasEstimados = s.estimado.filter(Boolean).length;

    return (
        <section className="pagina">
            <header className="pagina__cabecera">
                <div>
                    <p className="panel__saludo">Hola, {nombre}</p>
                    <h1>Panel de seguimiento</h1>
                    <p>
                        {tituloDia(s.hoy.fecha)} · día {s.dia_actual} de {s.plazo_dias} · meta{" "}
                        {num(s.peso_objetivo_kg)} kg el {fechaCorta(s.fecha_meta)}
                    </p>
                </div>
                <Link className="boton boton--primario pagina__accion" to="/calendario">
                    Registrar hoy
                </Link>
            </header>

            {s.desviacion.sugerir && (
                <article className="panel__aviso" role="status">
                    <div>
                        <h2>{s.desviacion.motivo}</h2>
                        <p>
                            Con {s.pesos.length - 1} pesos registrados, te sugerimos re-planear para
                            llegar a {num(s.peso_objetivo_kg)} kg con una ingesta ajustada a tu
                            progreso real.
                        </p>
                    </div>
                    <button
                        type="button"
                        className="boton boton--primario"
                        onClick={() => setReplaneando(true)}
                    >
                        Ver propuesta
                    </button>
                </article>
            )}

            <div className="kpis panel__kpis">
                <article className="kpi">
                    <span className="kpi__etiqueta">Ingesta del plan</span>
                    <span className="kpi__valor">
                        {num(plan.ingesta_kcal, 0)}
                        <small> kcal/día</small>
                    </span>
                    <br />
                    <span className="kpi__detalle">
                        {s.hoy.kcal === null
                            ? "Hoy aún no registras calorías"
                            : `Hoy: ${num(s.hoy.kcal, 0)} kcal (${conSigno(diferenciaHoy ?? 0, 0)})`}
                    </span>
                </article>
                <article className="kpi">
                    <span className="kpi__etiqueta">Peso actual</span>
                    <span className="kpi__valor">
                        {num(s.hoy.ultimo_peso_kg)}
                        <small> kg</small>
                    </span>
                    <br />
                    <span className="kpi__detalle">
                        {s.pesos.length > 1
                            ? `${conSigno(cambio)} kg desde el inicio`
                            : "Registra tu peso para ver el cambio"}
                    </span>
                </article>
                <article className="kpi">
                    <span className="kpi__etiqueta">Días restantes</span>
                    <span className="kpi__valor">{s.hoy.dias_restantes}</span>
                    <br/>
                    <span className="kpi__detalle">
                        Hoy el plan espera {num(s.hoy.peso_ideal_kg)} kg
                    </span>
                </article>
                <article className={`kpi${retraso !== null && retraso > 0 ? " kpi--alerta" : ""}`}>
                    <span className="kpi__etiqueta">Llegada estimada</span>
                    <span className="kpi__valor">
                        {s.llegada.dia !== null ? `Día ${s.llegada.dia}` : "Sin fecha"}
                    </span>
                    <br />
                    <span className="kpi__detalle">
                        {s.llegada.fecha ? `${fechaCorta(s.llegada.fecha)} · ` : ""}
                        {s.llegada.mensaje}
                    </span>
                </article>
            </div>

            <article className="tarjeta">
                <h2>Peso: plan, adherencia y realidad</h2>
                <GraficaSeguimiento key={s.plan_id} seguimiento={s} />
                <p className="tarjeta__nota">
                    Los puntos verdes son pesos registrados; los cuadrados marcan días estimados
                    por falta de calorías registradas. La proyección es aproximada.
                    {` ${s.pesos.length} pesos reales y ${diasEstimados} días estimados.`}
                    {s.tendencia &&
                        ` Tendencia: ${conSigno(s.tendencia.tasa_semanal_pct, 2)} % por semana; R² ${num(s.tendencia.r2, 2)} (n = ${s.tendencia.n} pesos).`}
                    {!s.tendencia &&
                        " La tendencia aparecerá cuando haya datos suficientes."}
                </p>
            </article>

            <div className="panel__dos">
                <article className="tarjeta">
                    <h2>Macros del día</h2>
                    <ul className="panel__macros">
                        <li>
                            <span>Proteína</span>
                            <strong>{num(plan.proteina_g, 0)} g</strong>
                        </li>
                        <li>
                            <span>Grasa</span>
                            <strong>{num(plan.grasa_g, 0)} g</strong>
                        </li>
                        <li>
                            <span>Carbohidratos</span>
                            <strong>{num(plan.carbohidratos_g, 0)} g</strong>
                        </li>
                    </ul>
                    <Link className="panel__enlace" to="/guia">
                        Ver reparto por comidas
                    </Link>
                </article>

                <article className="tarjeta">
                    <h2>Tu plan</h2>
                    <p>
                        De {num(plan.peso_inicial_kg)} kg a {num(plan.peso_objetivo_kg)} kg en{" "}
                        {plan.plazo_dias} días, desde el {fechaCorta(plan.fecha_inicio)}.
                        {!s.desviacion.sugerir && ` ${s.desviacion.motivo}`}
                    </p>
                    <div className="panel__acciones">
                        <Link className="panel__enlace" to="/plan/como-se-calculo">
                            Cómo se calculó
                        </Link>
                        <Link className="panel__enlace" to="/estadisticas">
                            Estadísticas
                        </Link>
                        <button
                            type="button"
                            className="panel__enlace panel__enlace--boton"
                            onClick={() => setReplaneando(true)}
                        >
                            Re-planear
                        </button>
                    </div>
                </article>
            </div>

            {replaneando && (
                <Replaneacion
                    onCerrar={() => setReplaneando(false)}
                    onReplaneado={() => {
                        setReplaneando(false);
                        setVersion((v) => v + 1);
                    }}
                />
            )}
        </section>
    );
}

function PanelSinPlan({ nombre }: { nombre: string }) {
    return (
        <section className="panel">
            <header className="panel__cabecera">
                <div>
                    <p className="panel__saludo">Hola, {nombre}</p>
                    <h1>Tu panel</h1>
                    <p className="panel__bajada">
                        Aquí verás tu plan activo, tus curvas de peso y el avance de la semana.
                    </p>
                </div>
            </header>

            <article className="panel__tarjeta panel__tarjeta--vacia">
                <div>
                    <span className="panel__etiqueta">Plan activo</span>
                    <h2>Todavía no tienes un plan</h2>
                    <p>
                        Define tu peso meta y la fecha en la que quieres llegar. Antes de
                        confirmar verás la ingesta, los macros y la curva estimada.
                    </p>
                </div>
                <Link className="panel__cta" to="/nuevo-plan">
                    Crear mi plan
                </Link>
            </article>

            <div className="panel__pasos">
                <article>
                    <strong>1</strong>
                    <h3>Completa tu perfil</h3>
                    <p>Revisa tu altura, actividad y nivel de entrenamiento.</p>
                    <Link to="/perfil">Ir a mi perfil</Link>
                </article>
                <article>
                    <strong>2</strong>
                    <h3>Calcula tu plan</h3>
                    <p>
                        La vista previa te muestra la viabilidad de la meta, los bloqueos y cómo
                        se calculó.
                    </p>
                    <Link to="/nuevo-plan">Nuevo plan</Link>
                </article>
                <article>
                    <strong>3</strong>
                    <h3>Registra tus días</h3>
                    <p>
                        Anota cada día tus calorías, tu peso y tu actividad física en el
                        calendario.
                    </p>
                    <Link to="/calendario">Ir al calendario</Link>
                </article>
            </div>
        </section>
    );
}
