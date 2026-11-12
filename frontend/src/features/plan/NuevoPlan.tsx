import { useState, type SubmitEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
    ArrowLeft,
    Calculator,
    ChartLine,
    CircleAlert,
    CircleCheck,
    Flame,
    Info,
    Pencil,
    Plus,
    Ruler,
    Save,
    Scale,
    Target,
    TrendingDown,
} from "lucide-react";

import { useSesion } from "../auth/SesionContext";
import { vistaPreviaPlan, confirmarPlan } from "./planService";
import type { VistaPreviaPlan, DatosPlan, TipoMeta } from "../../types/plan";
import {
    BloqueEsqueleto,
    EstadoEsqueleto,
    EsqueletoIndicadores,
    EsqueletoTabla,
} from "../../components/Esqueleto";
import ComoSeCalculo from "./ComoSeCalculo";
import { mensajeDeError } from "../../api/mensajeError";
import "../../styles/NuevoPlan.css";

type CampoPlan =
    | "pesoInicial"
    | "pesoMeta"
    | "grasaPerder"
    | "fechaInicio"
    | "fechaMeta"
    | "cuello"
    | "cintura"
    | "cadera";

type ErroresPlan = Partial<Record<CampoPlan, string>>;

function fechaHoyLocal() {
    const hoy = new Date();
    hoy.setMinutes(hoy.getMinutes() - hoy.getTimezoneOffset());
    return hoy.toISOString().slice(0, 10);
}

function diasEntre(inicio: string, meta: string): number | null {
    const [anioInicio, mesInicio, diaInicio] = inicio.split("-").map(Number);
    const [anioMeta, mesMeta, diaMeta] = meta.split("-").map(Number);
    const fechaInicio = Date.UTC(anioInicio, mesInicio - 1, diaInicio);
    const fechaMeta = Date.UTC(anioMeta, mesMeta - 1, diaMeta);
    const dias = (fechaMeta - fechaInicio) / 86_400_000;

    return Number.isFinite(dias) ? dias : null;
}

function validarCampos(datos: {
    pesoInicial: string;
    tipoMeta: TipoMeta;
    pesoMeta: string;
    grasaPerder: string;
    fechaInicio: string;
    fechaMeta: string;
    cuello: string;
    cintura: string;
    cadera: string;
    esMujer: boolean;
}): ErroresPlan {
    const errores: ErroresPlan = {};
    const pesoInicial = Number(datos.pesoInicial);
    const pesoMeta = Number(datos.pesoMeta);
    const cuello = datos.cuello === "" ? null : Number(datos.cuello);
    const cintura = datos.cintura === "" ? null : Number(datos.cintura);
    const cadera = datos.cadera === "" ? null : Number(datos.cadera);

    if (!datos.pesoInicial) {
        errores.pesoInicial = "Ingresa tu peso actual.";
    } else if (!Number.isFinite(pesoInicial) || pesoInicial < 30 || pesoInicial > 300) {
        errores.pesoInicial = "El peso debe estar entre 30 y 300 kg.";
    }

    if (datos.tipoMeta === "grasa") {
        const grasa = Number(datos.grasaPerder);
        if (!datos.grasaPerder) {
            errores.grasaPerder = "Ingresa cuántos kg de grasa quieres perder.";
        } else if (!Number.isFinite(grasa) || grasa <= 0 || grasa > 100) {
            errores.grasaPerder = "Debe ser un número mayor que 0 y hasta 100 kg.";
        } else if (Number.isFinite(pesoInicial) && grasa >= pesoInicial) {
            errores.grasaPerder = "La grasa a perder debe ser menor que tu peso.";
        }
    } else if (!datos.pesoMeta) {
        errores.pesoMeta = "Ingresa tu peso objetivo.";
    } else if (!Number.isFinite(pesoMeta) || pesoMeta < 30 || pesoMeta > 300) {
        errores.pesoMeta = "El peso debe estar entre 30 y 300 kg.";
    } else if (Number.isFinite(pesoInicial) && pesoMeta >= pesoInicial) {
        errores.pesoMeta = "El peso objetivo debe ser menor que el peso inicial.";
    }

    if (!datos.fechaInicio) {
        errores.fechaInicio = "Selecciona la fecha de inicio.";
    } else if (datos.fechaInicio > fechaHoyLocal()) {
        errores.fechaInicio = "La fecha de inicio no puede ser futura.";
    }

    if (!datos.fechaMeta) {
        errores.fechaMeta = "Selecciona la fecha objetivo.";
    } else if (datos.fechaInicio && datos.fechaMeta) {
        const plazo = diasEntre(datos.fechaInicio, datos.fechaMeta);
        if (plazo === null || plazo <= 0) {
            errores.fechaMeta = "La fecha objetivo debe ser posterior al inicio.";
        } else if (plazo < 2) {
            errores.fechaMeta = "El plazo debe ser de al menos 2 días.";
        } else if (plazo > 730) {
            errores.fechaMeta = "El plazo no puede superar 730 días.";
        }
    }

    if (cuello !== null && (!Number.isFinite(cuello) || cuello < 20 || cuello > 250)) {
        errores.cuello = "El cuello debe estar entre 20 y 250 cm.";
    }
    if (cintura !== null && (!Number.isFinite(cintura) || cintura < 30 || cintura > 250)) {
        errores.cintura = "La cintura debe estar entre 30 y 250 cm.";
    }
    if (datos.esMujer && cadera !== null && (!Number.isFinite(cadera) || cadera < 30 || cadera > 250)) {
        errores.cadera = "La cadera debe estar entre 30 y 250 cm.";
    }

    const medidasValidas =
        cuello !== null &&
        cintura !== null &&
        Number.isFinite(cuello) &&
        Number.isFinite(cintura) &&
        (datos.esMujer
            ? cadera !== null && Number.isFinite(cadera)
            : true);
    if (medidasValidas && datos.esMujer && cintura + (cadera ?? 0) <= cuello) {
        errores.cadera = "Revisa las medidas: cintura + cadera debe ser mayor que cuello.";
    } else if (medidasValidas && !datos.esMujer && cintura <= cuello) {
        errores.cintura = "La cintura debe ser mayor que el cuello para usar estas medidas.";
    }

    return errores;
}

export default function NuevoPlan() {
    const { usuario } = useSesion();
    const navegar = useNavigate();

    const [pesoInicial, setPesoInicial] = useState("");
    const [tipoMeta, setTipoMeta] = useState<TipoMeta>("peso");
    const [pesoMeta, setPesoMeta] = useState("");
    const [grasaPerder, setGrasaPerder] = useState("");
    const [fechaInicio, setFechaInicio] = useState(fechaHoyLocal);
    const [fechaMeta, setFechaMeta] = useState("");
    const [cuello, setCuello] = useState("");
    const [cintura, setCintura] = useState("");
    const [cadera, setCadera] = useState("");

    const [previa, setPrevia] = useState<VistaPreviaPlan | null>(null);
    const [datosPrevia, setDatosPrevia] = useState<DatosPlan | null>(null);
    const [cargando, setCargando] = useState(false);
    const [confirmando, setConfirmando] = useState(false);
    const [error, setError] = useState("");
    const [camposTocados, setCamposTocados] = useState<Partial<Record<CampoPlan, boolean>>>({});
    const [intentoEnviar, setIntentoEnviar] = useState(false);

    const esMujer = usuario?.sexo === "Femenino";

    const errores = validarCampos({
        pesoInicial,
        tipoMeta,
        pesoMeta,
        grasaPerder,
        fechaInicio,
        fechaMeta,
        cuello,
        cintura,
        cadera,
        esMujer,
    });

    function marcarCampoTocado(campo: CampoPlan) {
        setCamposTocados((actuales) => ({ ...actuales, [campo]: true }));
    }

    function errorVisible(campo: CampoPlan) {
        return (camposTocados[campo] || intentoEnviar) ? errores[campo] : undefined;
    }

    function actualizarCampo(campo: CampoPlan, actualizar: (valor: string) => void, valor: string) {
        actualizar(valor);
        marcarCampoTocado(campo);
        invalidarPrevia();
    }

    function invalidarPrevia() {
        setPrevia(null);
        setDatosPrevia(null);
        setError("");
    }

    function cambiarTipoMeta(tipo: TipoMeta) {
        setTipoMeta(tipo);
        invalidarPrevia();
    }

    function usarMetaEnGrasa(kg: number) {
        setTipoMeta("grasa");
        setGrasaPerder(String(kg));
        invalidarPrevia();
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function construirDatos(): DatosPlan {
        return {
            peso_inicial_kg: Number(pesoInicial),
            tipo_meta: tipoMeta,
            ...(tipoMeta === "grasa"
                ? { grasa_a_perder_kg: Number(grasaPerder) }
                : { peso_objetivo_kg: Number(pesoMeta) }),
            fecha_inicio: fechaInicio,
            fecha_meta: fechaMeta,
            cuello_cm: cuello ? Number(cuello) : undefined,
            cintura_cm: cintura ? Number(cintura) : undefined,
            cadera_cm: esMujer && cadera ? Number(cadera) : undefined,
        };
    }

    async function enviar(event: SubmitEvent<HTMLFormElement>) {
        event.preventDefault();
        setIntentoEnviar(true);
        setError("");
        const camposInvalidos = Object.keys(errores) as CampoPlan[];
        if (camposInvalidos.length > 0) {
            setCamposTocados((actuales) => ({
                ...actuales,
                ...Object.fromEntries(camposInvalidos.map((campo) => [campo, true])),
            }));
            return;
        }
        setPrevia(null);
        setDatosPrevia(null);
        setCargando(true);
        try {
            const datos = construirDatos();
            const resultado = await vistaPreviaPlan(datos);
            setPrevia(resultado);
            setDatosPrevia(datos);
        } catch (error) {
            setError(mensajeDeError(error));
        } finally {
            setCargando(false);
        }
    }

    async function confirmar() {
        if (!previa?.puede_confirmar || !datosPrevia) return;
        setConfirmando(true);
        setError("");
        try {
            await confirmarPlan(datosPrevia);
            navegar("/panel", { replace: true });
        } catch (error) {
            setError(mensajeDeError(error));
        } finally {
            setConfirmando(false);
        }
    }

    return (
        <section className="nuevo-plan">
            <header className="nuevo-plan__cabecera">
                <span className="nuevo-plan__eyebrow">Tu siguiente paso</span>
                <h1>
                    <Plus className="icono-ui" size={21} aria-hidden="true" />
                    Nuevo plan
                </h1>
                <p>
                    Define una meta realista. Revisaremos la viabilidad y tus
                    objetivos de nutrición antes de guardar el plan.
                </p>
            </header>

            {!previa?.puede_confirmar && (
                <form
                    className="nuevo-plan__formulario"
                    onSubmit={enviar}
                    noValidate
                    aria-busy={cargando}
                >
                <section className="nuevo-plan__grupo" aria-labelledby="nuevo-plan-meta">
                    <div className="nuevo-plan__grupo-cabecera">
                        <span className="nuevo-plan__paso">01</span>
                        <div>
                            <h2 id="nuevo-plan-meta" className="nuevo-plan__titulo-icono">
                                <Target className="icono-ui" size={19} aria-hidden="true" />
                                Tu objetivo
                            </h2>
                            <p>Indica desde dónde empiezas y a dónde quieres llegar.</p>
                        </div>
                    </div>
                    <div className="nuevo-plan__tipo-meta" role="radiogroup" aria-label="Tipo de meta">
                        <button
                            type="button"
                            role="radio"
                            aria-checked={tipoMeta === "peso"}
                            className={tipoMeta === "peso" ? "activo" : ""}
                            onClick={() => cambiarTipoMeta("peso")}
                        >
                            Meta en peso
                        </button>
                        <button
                            type="button"
                            role="radio"
                            aria-checked={tipoMeta === "grasa"}
                            className={tipoMeta === "grasa" ? "activo" : ""}
                            onClick={() => cambiarTipoMeta("grasa")}
                        >
                            Meta en grasa
                        </button>
                    </div>
                    {tipoMeta === "grasa" && (
                        <p className="nuevo-plan__ayuda-meta">
                            Al bajar de peso también se pierde algo de músculo y agua. Dinos
                            cuánta grasa quieres perder y calculamos el peso al que llegarías.
                        </p>
                    )}
                    <div className="nuevo-plan__grid nuevo-plan__grid--meta">
                        <label className={errorVisible("pesoInicial") ? "nuevo-plan__campo--invalido" : ""}>
                            Peso inicial <span>(kg)</span>
                            <input
                                aria-invalid={Boolean(errorVisible("pesoInicial"))}
                                aria-describedby={errorVisible("pesoInicial") ? "error-peso-inicial" : undefined}
                                type="number"
                                min="30"
                                max="300"
                                step="0.1"
                                value={pesoInicial}
                                onChange={(e) => {
                                    actualizarCampo("pesoInicial", setPesoInicial, e.target.value);
                                }}
                            />
                            {errorVisible("pesoInicial") && <span className="nuevo-plan__error-campo" id="error-peso-inicial">{errorVisible("pesoInicial")}</span>}
                        </label>
                        {tipoMeta === "grasa" ? (
                        <label className={errorVisible("grasaPerder") ? "nuevo-plan__campo--invalido" : ""}>
                            Grasa a perder <span>(kg)</span>
                            <input
                                aria-invalid={Boolean(errorVisible("grasaPerder"))}
                                aria-describedby={errorVisible("grasaPerder") ? "error-grasa-perder" : undefined}
                                type="number"
                                min="0.5"
                                max="100"
                                step="0.1"
                                value={grasaPerder}
                                onChange={(e) => {
                                    actualizarCampo("grasaPerder", setGrasaPerder, e.target.value);
                                }}
                            />
                            {errorVisible("grasaPerder") && <span className="nuevo-plan__error-campo" id="error-grasa-perder">{errorVisible("grasaPerder")}</span>}
                        </label>
                        ) : (
                        <label className={errorVisible("pesoMeta") ? "nuevo-plan__campo--invalido" : ""}>
                            Peso meta <span>(kg)</span>
                            <input
                                aria-invalid={Boolean(errorVisible("pesoMeta"))}
                                aria-describedby={errorVisible("pesoMeta") ? "error-peso-meta" : undefined}
                                type="number"
                                min="30"
                                max="300"
                                step="0.1"
                                value={pesoMeta}
                                onChange={(e) => {
                                    actualizarCampo("pesoMeta", setPesoMeta, e.target.value);
                                }}
                            />
                            {errorVisible("pesoMeta") && <span className="nuevo-plan__error-campo" id="error-peso-meta">{errorVisible("pesoMeta")}</span>}
                        </label>
                        )}
                        <label className={errorVisible("fechaInicio") ? "nuevo-plan__campo--invalido" : ""}>
                            Fecha de inicio
                            <input
                                aria-invalid={Boolean(errorVisible("fechaInicio"))}
                                aria-describedby={errorVisible("fechaInicio") ? "error-fecha-inicio" : undefined}
                                type="date"
                                value={fechaInicio}
                                onChange={(e) => {
                                    actualizarCampo("fechaInicio", setFechaInicio, e.target.value);
                                }}
                            />
                            {errorVisible("fechaInicio") && <span className="nuevo-plan__error-campo" id="error-fecha-inicio">{errorVisible("fechaInicio")}</span>}
                        </label>
                        <label className={errorVisible("fechaMeta") ? "nuevo-plan__campo--invalido" : ""}>
                            Fecha objetivo
                            <input
                                aria-invalid={Boolean(errorVisible("fechaMeta"))}
                                aria-describedby={errorVisible("fechaMeta") ? "error-fecha-meta" : undefined}
                                type="date"
                                value={fechaMeta}
                                onChange={(e) => {
                                    actualizarCampo("fechaMeta", setFechaMeta, e.target.value);
                                }}
                            />
                            {errorVisible("fechaMeta") && <span className="nuevo-plan__error-campo" id="error-fecha-meta">{errorVisible("fechaMeta")}</span>}
                        </label>
                    </div>
                </section>

                <section className="nuevo-plan__grupo nuevo-plan__grupo--medidas" aria-labelledby="nuevo-plan-medidas">
                    <div className="nuevo-plan__grupo-cabecera">
                        <span className="nuevo-plan__paso">02</span>
                        <div>
                            <h2 id="nuevo-plan-medidas" className="nuevo-plan__titulo-icono">
                                <Ruler className="icono-ui" size={19} aria-hidden="true" />
                                Medidas corporales <span>Opcional</span>
                            </h2>
                            <p>
                                Ayudan a estimar tu composición. Si las dejas vacías o incompletas,
                                usaremos una estimación basada en tu perfil.
                            </p>
                        </div>
                    </div>
                    <div className="nuevo-plan__grid nuevo-plan__grid--medidas">
                        <label className={errorVisible("cuello") ? "nuevo-plan__campo--invalido" : ""}>
                            Cuello <span>(cm, opcional)</span>
                            <input
                                aria-invalid={Boolean(errorVisible("cuello"))}
                                aria-describedby={errorVisible("cuello") ? "error-cuello" : undefined}
                                type="number"
                                min="20"
                                max="250"
                                step="0.1"
                                value={cuello}
                                onChange={(e) => {
                                    actualizarCampo("cuello", setCuello, e.target.value);
                                }}
                            />
                            {errorVisible("cuello") && <span className="nuevo-plan__error-campo" id="error-cuello">{errorVisible("cuello")}</span>}
                        </label>
                        <label className={errorVisible("cintura") ? "nuevo-plan__campo--invalido" : ""}>
                            Cintura <span>(cm, opcional)</span>
                            <input
                                aria-invalid={Boolean(errorVisible("cintura"))}
                                aria-describedby={errorVisible("cintura") ? "error-cintura" : undefined}
                                type="number"
                                min="30"
                                max="250"
                                step="0.1"
                                value={cintura}
                                onChange={(e) => {
                                    actualizarCampo("cintura", setCintura, e.target.value);
                                }}
                            />
                            {errorVisible("cintura") && <span className="nuevo-plan__error-campo" id="error-cintura">{errorVisible("cintura")}</span>}
                        </label>
                        {esMujer && (
                            <label className={errorVisible("cadera") ? "nuevo-plan__campo--invalido" : ""}>
                                Cadera <span>(cm, opcional)</span>
                                <input
                                    aria-invalid={Boolean(errorVisible("cadera"))}
                                    aria-describedby={errorVisible("cadera") ? "error-cadera" : undefined}
                                    type="number"
                                    min="30"
                                    max="250"
                                    step="0.1"
                                    value={cadera}
                                    onChange={(e) => {
                                        actualizarCampo("cadera", setCadera, e.target.value);
                                    }}
                                />
                                {errorVisible("cadera") && <span className="nuevo-plan__error-campo" id="error-cadera">{errorVisible("cadera")}</span>}
                            </label>
                        )}
                    </div>
                </section>

                <div className="nuevo-plan__acciones">
                    <button
                        type="submit"
                        className="boton boton--primario"
                        disabled={cargando || confirmando}
                    >
                        <Calculator size={17} aria-hidden="true" />
                        {cargando ? "Calculando la vista previa..." : "Ver vista previa del plan"}
                    </button>
                    <Link className="boton boton--secundario " to="/panel">
                        <ArrowLeft size={16} aria-hidden="true" />
                        Volver al panel
                    </Link>
                </div>
                <p className="nuevo-plan__nota-previa">
                    Esto calcula la viabilidad de tu meta. El plan solo se guarda
                    cuando confirmes el resultado.
                </p>
                </form>
            )}

            {cargando && (
                <EstadoEsqueleto
                    mensaje="Calculando la vista previa de tu plan..."
                    className="nuevo-plan__carga-previa"
                >
                    <article className="esqueleto__tarjeta">
                        <BloqueEsqueleto className="esqueleto__subtitulo" />
                        <EsqueletoTabla filas={3} columnas={2} />
                    </article>
                    <EsqueletoIndicadores cantidad={3} />
                    <article className="esqueleto__tarjeta">
                        <BloqueEsqueleto className="esqueleto__subtitulo" />
                        <BloqueEsqueleto className="esqueleto__grafica" />
                    </article>
                </EstadoEsqueleto>
            )}

            {error && (
                <p className="nuevo-plan__error" role="alert">
                    <strong>No pudimos completar la solicitud.</strong>
                    <span>{error}</span>
                </p>
            )}

            {previa && (
                <div className="nuevo-plan__resultado">
                    <section
                        className={`nuevo-plan__resumen${previa.puede_confirmar ? " nuevo-plan__resumen--listo" : ""}`}
                        aria-labelledby="nuevo-plan-resumen"
                    >
                        <div>
                            <span className="nuevo-plan__eyebrow">
                                Resultado de la vista previa
                            </span>
                            <h2 id="nuevo-plan-resumen">
                                {previa.puede_confirmar ? (
                                    <CircleCheck className="icono-ui" size={20} aria-hidden="true" />
                                ) : (
                                    <CircleAlert className="icono-ui" size={20} aria-hidden="true" />
                                )}
                                {previa.puede_confirmar
                                    ? "Tu plan está listo para confirmar"
                                    : "Revisa la viabilidad de esta meta"}
                            </h2>
                            <p>{previa.viabilidad.mensaje}</p>
                        </div>
                        <dl>
                            <div>
                                <dt>Meta</dt>
                                <dd>
                                    {previa.meta?.tipo === "grasa"
                                        ? `${previa.meta.grasa_a_perder_kg ?? "—"} kg de grasa · ${previa.meta.peso_objetivo_kg.toFixed(1)} kg de peso`
                                        : previa.meta
                                            ? `${previa.meta.peso_objetivo_kg.toFixed(1)} kg`
                                            : "No disponible"}
                                </dd>
                            </div>
                            <div>
                                <dt>Plazo</dt>
                                <dd>{previa.plazo_dias} días</dd>
                            </div>
                            <div>
                                <dt>Fechas</dt>
                                <dd>
                                    {previa.fecha_inicio} – {previa.fecha_meta}
                                </dd>
                            </div>
                            <div>
                                <dt>Fecha viable</dt>
                                <dd>{previa.viabilidad.fecha_viable ?? "—"}</dd>
                            </div>
                            <div>
                                <dt>Ingesta diaria</dt>
                                <dd>
                                    {previa.ingesta_kcal !== null
                                        ? `${previa.ingesta_kcal.toFixed(0)} kcal`
                                        : "Pendiente de viabilidad"}
                                </dd>
                            </div>
                        </dl>
                    </section>

                    {previa.puede_confirmar && (
                        <div className="nuevo-plan__acciones-navegacion">
                            <p>Tu plan está listo para guardar. Revisa el resumen y confirma cuando quieras.</p>
                            <button
                                type="button"
                                className="boton boton--secundario"
                                onClick={invalidarPrevia}
                                disabled={confirmando}
                            >
                                <Pencil size={16} aria-hidden="true" />
                                Editar datos
                            </button>
                        </div>
                    )}
                    {previa.meta?.tipo === "grasa" && previa.meta.grasa_a_perder_kg !== null && (
                        <section className="nuevo-plan__tarjeta nuevo-plan__tarjeta--grasa">
                            <h2 className="nuevo-plan__titulo-icono">
                                <Target className="icono-ui" size={18} aria-hidden="true" />
                                Tu meta
                            </h2>
                            <p>
                                Perder {previa.meta.grasa_a_perder_kg.toFixed(1)} kg de grasa te
                                lleva a unos <strong>{previa.meta.peso_objetivo_kg.toFixed(1)} kg</strong>.
                                La diferencia es la masa libre que se pierde junto con la grasa.
                            </p>
                        </section>
                    )}

                    <section className="nuevo-plan__tarjeta">
                        <h2 className="nuevo-plan__titulo-icono">
                            <Scale className="icono-ui" size={18} aria-hidden="true" />
                            Composición inicial
                        </h2>
                        <p>
                            {previa.composicion.pct_grasa.toFixed(1)} % de grasa
                            ({previa.composicion.metodo}). Masa libre:{" "}
                            {previa.composicion.masa_libre_inicial_kg.toFixed(1)}{" "}
                            kg.
                        </p>
                    </section>

                    {previa.bloqueos.length > 0 && (
                        <section className="nuevo-plan__bloqueos">
                            <h2 className="nuevo-plan__titulo-icono">
                                <CircleAlert className="icono-ui" size={18} aria-hidden="true" />
                                Bloqueos
                            </h2>
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
                            <h2 className="nuevo-plan__titulo-icono">
                                <Info className="icono-ui" size={18} aria-hidden="true" />
                                Avisos
                            </h2>
                            <ul>
                                {previa.advertencias.map((a, i) => (
                                    <li key={i}>{a}</li>
                                ))}
                            </ul>
                        </section>
                    )}

                    {previa.equivalente_grasa && (
                        <section className="nuevo-plan__tarjeta nuevo-plan__tarjeta--grasa">
                            <h2>
                                ¿Y si quieres perder{" "}
                                {previa.equivalente_grasa.grasa_a_perder_kg.toFixed(1)} kg de grasa?
                            </h2>
                            <p>
                                Al bajar de peso también se pierde masa libre (músculo y su
                                agua). Para que esos{" "}
                                {previa.equivalente_grasa.grasa_a_perder_kg.toFixed(1)} kg sean
                                de grasa, la meta tendría que ser de unos{" "}
                                <strong>{previa.equivalente_grasa.peso_meta_kg.toFixed(1)} kg</strong>{" "}
                                (IMC {previa.equivalente_grasa.imc_meta.toFixed(1)},{" "}
                                {previa.equivalente_grasa.pct_grasa_final.toFixed(1)} % de grasa
                                al final).
                            </p>
                            {previa.equivalente_grasa.segura ? (
                                <button
                                    type="button"
                                    className="boton boton--secundario nuevo-plan__usar-grasa"
                                    onClick={() => usarMetaEnGrasa(previa.equivalente_grasa!.grasa_a_perder_kg)}
                                >
                                    <Target size={16} aria-hidden="true" />
                                    Usar meta en grasa
                                </button>
                            ) : (
                                <p className="nuevo-plan__nota-alerta">
                                    Esa meta queda por debajo de un nivel seguro de grasa
                                    corporal o de IMC, así que no la recomendamos.
                                </p>
                            )}
                        </section>
                    )}

                    {previa.puede_confirmar && previa.ingesta_kcal && (
                        <>
                            <section className="nuevo-plan__tarjeta">
                                <h2 className="nuevo-plan__titulo-icono">
                                    <Flame className="icono-ui" size={18} aria-hidden="true" />
                                    Ingesta diaria
                                </h2>
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
                                    <h2 className="nuevo-plan__titulo-icono">
                                        <TrendingDown className="icono-ui" size={18} aria-hidden="true" />
                                        Pérdida estimada
                                    </h2>
                                    <p>
                                        Peso {previa.perdida.peso_kg.toFixed(1)} kg ·
                                        Grasa {previa.perdida.grasa_kg.toFixed(1)} kg ·
                                        Masa libre{" "}
                                        {previa.perdida.masa_libre_kg.toFixed(1)} kg
                                    </p>
                                </section>
                            )}

                            <section className="nuevo-plan__grafica">
                                <h2 className="nuevo-plan__titulo-icono">
                                    <ChartLine className="icono-ui" size={18} aria-hidden="true" />
                                    Curva ideal
                                </h2>
                                {/* Recharts importado en ComoSeCalculo; aquí resumen textual */}
                                {previa.curva && previa.curva.peso_kg.length > 0 ? (
                                    <p>
                                        El peso pasa de{" "}
                                        {previa.curva.peso_kg[0].toFixed(1)} kg a{" "}
                                        {previa.curva.peso_kg[previa.curva.peso_kg.length - 1].toFixed(1)}{" "}
                                        kg en {previa.plazo_dias} días, con una banda de
                                        tolerancia de 1 kg.
                                    </p>
                                ) : (
                                    <p>
                                        La curva llega a la meta en {previa.plazo_dias} días,
                                        con una banda de tolerancia de 1 kg.
                                    </p>
                                )}
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
                                    <Save size={16} aria-hidden="true" />
                                    {confirmando ? "Guardando tu plan..." : "Confirmar y guardar plan"}
                                </button>
                            </div>
                        </>
                    )}
                </div>
            )}
        </section>
    );
}
