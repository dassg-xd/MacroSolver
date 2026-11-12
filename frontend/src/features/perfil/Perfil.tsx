import { useRef, useState, type SubmitEvent } from "react";

import { mensajeDeError } from "../../api/mensajeError";
import type { DatosPerfil, UsuarioPublico } from "../../types/auth";
import { useSesion } from "../auth/SesionContext";
import "../../styles/Perfil.css";

const FACTORES = ["1.2", "1.375", "1.55", "1.725", "1.9"];

type CampoPerfil = keyof FormularioPerfil;
type ErroresPerfil = Partial<Record<CampoPerfil, string>>;

interface FormularioPerfil {
    nombre: string;
    sexo: UsuarioPublico["sexo"];
    fecha_nacimiento: string;
    altura_cm: string;
    factor_actividad: string;
    nivel_entrenamiento: UsuarioPublico["nivel_entrenamiento"];
}

function datosDesde(usuario: UsuarioPublico | null): FormularioPerfil {
    return {
        nombre: usuario?.nombre ?? "",
        sexo: usuario?.sexo ?? "Femenino",
        fecha_nacimiento: usuario?.fecha_nacimiento ?? "",
        altura_cm: usuario ? String(usuario.altura_cm) : "",
        factor_actividad: usuario ? String(usuario.factor_actividad) : "1.375",
        nivel_entrenamiento: usuario?.nivel_entrenamiento ?? "principiante",
    };
}

function calcularEdad(fecha: string): number | null {
    const nacimiento = new Date(`${fecha}T00:00:00`);
    if (!fecha || Number.isNaN(nacimiento.getTime())) {
        return null;
    }

    const hoy = new Date();
    let edad = hoy.getFullYear() - nacimiento.getFullYear();
    const mes = hoy.getMonth() - nacimiento.getMonth();
    if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
        edad -= 1;
    }
    return edad;
}

export default function Perfil() {
    const { usuario, actualizarPerfil } = useSesion();
    const [formulario, setFormulario] = useState<FormularioPerfil>(() =>
        datosDesde(usuario)
    );
    const [guardando, setGuardando] = useState(false);
    const [error, setError] = useState("");
    const [exito, setExito] = useState("");
    const [aviso, setAviso] = useState("");
    const [erroresCampos, setErroresCampos] = useState<ErroresPerfil>({});
    const nombreRef = useRef<HTMLInputElement>(null);
    const fechaRef = useRef<HTMLInputElement>(null);
    const alturaRef = useRef<HTMLInputElement>(null);
    const factorRef = useRef<HTMLSelectElement>(null);

    if (!usuario) {
        return null;
    }

    const perfilActual = usuario;
    const edad = calcularEdad(formulario.fecha_nacimiento);

    function cambiar<K extends keyof FormularioPerfil>(
        campo: K,
        valor: FormularioPerfil[K]
    ) {
        setFormulario((actual) => ({ ...actual, [campo]: valor }));
        setErroresCampos((actuales) => ({ ...actuales, [campo]: undefined }));
        setError("");
        setExito("");
        setAviso("");
    }

    async function enviar(event: SubmitEvent<HTMLFormElement>) {
        event.preventDefault();
        if (guardando) {
            return;
        }
        setError("");
        setExito("");
        setAviso("");

        const nombre = formulario.nombre.trim();
        const altura = Number(formulario.altura_cm);
        const nuevosErrores: ErroresPerfil = {};

        if (!nombre) {
            nuevosErrores.nombre = "Ingresa tu nombre.";
        }
        if (!Number.isFinite(altura) || altura < 100 || altura > 250) {
            nuevosErrores.altura_cm = "Escribe una altura entre 100 y 250 cm.";
        }
        if (!formulario.fecha_nacimiento || edad === null || edad < 18) {
            nuevosErrores.fecha_nacimiento =
                "Debes tener al menos 18 años para usar MacroSolver.";
        }
        if (!FACTORES.includes(formulario.factor_actividad)) {
            nuevosErrores.factor_actividad =
                "Elige un factor de actividad válido.";
        }

        setErroresCampos(nuevosErrores);
        if (Object.keys(nuevosErrores).length > 0) {
            setError("Revisa los campos marcados.");
            if (nuevosErrores.nombre) {
                nombreRef.current?.focus();
            } else if (nuevosErrores.fecha_nacimiento) {
                fechaRef.current?.focus();
            } else if (nuevosErrores.altura_cm) {
                alturaRef.current?.focus();
            } else {
                factorRef.current?.focus();
            }
            return;
        }

        const cambios: DatosPerfil = {};
        if (nombre !== perfilActual.nombre) cambios.nombre = nombre;
        if (formulario.sexo !== perfilActual.sexo) cambios.sexo = formulario.sexo;
        if (formulario.fecha_nacimiento !== perfilActual.fecha_nacimiento) {
            cambios.fecha_nacimiento = formulario.fecha_nacimiento;
        }
        if (altura !== Number(perfilActual.altura_cm)) cambios.altura_cm = altura;
        if (
            Number(formulario.factor_actividad) !==
            Number(perfilActual.factor_actividad)
        ) {
            cambios.factor_actividad = Number(formulario.factor_actividad);
        }
        if (
            formulario.nivel_entrenamiento !== perfilActual.nivel_entrenamiento
        ) {
            cambios.nivel_entrenamiento = formulario.nivel_entrenamiento;
        }

        if (Object.keys(cambios).length === 0) {
            setAviso("No hay cambios por guardar.");
            return;
        }

        setGuardando(true);
        try {
            const perfil = await actualizarPerfil(cambios);
            setFormulario(datosDesde(perfil));
            setExito("Perfil actualizado. Los próximos planes usarán estos datos.");
        } catch (errorPerfil: unknown) {
            setError(mensajeDeError(errorPerfil));
        } finally {
            setGuardando(false);
        }
    }

    return (
        <section className="perfil">
            <header className="perfil__cabecera">
                <p className="perfil__saludo">Mi perfil</p>
                <h1>Tus datos</h1>
                <p>
                    Estos datos alimentan el cálculo de tu gasto energético. Los
                    cambios aplican a los planes que crees después; el plan activo
                    conserva la copia con la que se creó.
                </p>
            </header>

            <form className="perfil__tarjeta" onSubmit={enviar}>
                <div className="perfil__fila">
                    <div>
                        <label htmlFor="nombre">Nombre</label>
                        <input
                            id="nombre"
                            ref={nombreRef}
                            value={formulario.nombre}
                            maxLength={150}
                            autoComplete="name"
                            aria-invalid={Boolean(erroresCampos.nombre)}
                            aria-describedby={
                                erroresCampos.nombre ? "perfil-error-nombre" : undefined
                            }
                            onChange={(evento) =>
                                cambiar("nombre", evento.target.value)
                            }
                        />
                        {erroresCampos.nombre && (
                            <p id="perfil-error-nombre" className="perfil__error-campo">
                                {erroresCampos.nombre}
                            </p>
                        )}
                    </div>
                    <div>
                        <label htmlFor="correo">Correo</label>
                        <input id="correo" value={usuario.correo} readOnly />
                    </div>
                </div>

                <div className="perfil__fila">
                    <div>
                        <label htmlFor="sexo">Sexo</label>
                        <select
                            id="sexo"
                            value={formulario.sexo}
                            onChange={(evento) =>
                                cambiar(
                                    "sexo",
                                    evento.target.value as UsuarioPublico["sexo"]
                                )
                            }
                        >
                            <option value="Femenino">Femenino</option>
                            <option value="Masculino">Masculino</option>
                        </select>
                    </div>
                    <div>
                        <label htmlFor="fechaNacimiento">Fecha de nacimiento</label>
                        <input
                            id="fechaNacimiento"
                            ref={fechaRef}
                            type="date"
                            value={formulario.fecha_nacimiento}
                            aria-invalid={Boolean(erroresCampos.fecha_nacimiento)}
                            aria-describedby={
                                erroresCampos.fecha_nacimiento
                                    ? "perfil-error-fecha"
                                    : undefined
                            }
                            onChange={(evento) =>
                                cambiar("fecha_nacimiento", evento.target.value)
                            }
                        />
                        {erroresCampos.fecha_nacimiento && (
                            <p id="perfil-error-fecha" className="perfil__error-campo">
                                {erroresCampos.fecha_nacimiento}
                            </p>
                        )}
                        {edad !== null && (
                            <p className="perfil__ayuda">{edad} años</p>
                        )}
                    </div>
                </div>

                <div className="perfil__fila">
                    <div>
                        <label htmlFor="altura">Altura (cm)</label>
                        <input
                            id="altura"
                            ref={alturaRef}
                            type="number"
                            min="100"
                            max="250"
                            step="0.1"
                            inputMode="decimal"
                            value={formulario.altura_cm}
                            aria-invalid={Boolean(erroresCampos.altura_cm)}
                            aria-describedby={
                                erroresCampos.altura_cm ? "perfil-error-altura" : undefined
                            }
                            onChange={(evento) =>
                                cambiar("altura_cm", evento.target.value)
                            }
                        />
                        {erroresCampos.altura_cm && (
                            <p id="perfil-error-altura" className="perfil__error-campo">
                                {erroresCampos.altura_cm}
                            </p>
                        )}
                    </div>
                    <div>
                        <label htmlFor="factorActividad">Nivel de actividad</label>
                        <select
                            ref={factorRef}
                            id="factorActividad"
                            value={formulario.factor_actividad}
                            aria-invalid={Boolean(erroresCampos.factor_actividad)}
                            aria-describedby={
                                erroresCampos.factor_actividad
                                    ? "perfil-error-factor"
                                    : undefined
                            }
                            onChange={(evento) =>
                                cambiar("factor_actividad", evento.target.value)
                            }
                        >
                            <option value="1.2">Sedentario · 1,2</option>
                            <option value="1.375">Ligero · 1,375</option>
                            <option value="1.55">Moderado · 1,55</option>
                            <option value="1.725">Activo · 1,725</option>
                            <option value="1.9">Muy activo · 1,9</option>
                        </select>
                        {erroresCampos.factor_actividad && (
                            <p id="perfil-error-factor" className="perfil__error-campo">
                                {erroresCampos.factor_actividad}
                            </p>
                        )}
                    </div>
                </div>

                <label htmlFor="nivelEntrenamiento">Nivel de entrenamiento</label>
                <select
                    id="nivelEntrenamiento"
                    value={formulario.nivel_entrenamiento}
                    onChange={(evento) =>
                        cambiar(
                            "nivel_entrenamiento",
                            evento.target
                                .value as UsuarioPublico["nivel_entrenamiento"]
                        )
                    }
                >
                    <option value="principiante">Principiante</option>
                    <option value="intermedio">Intermedio</option>
                    <option value="avanzado">Avanzado</option>
                </select>

                {error && (
                    <p className="perfil__alerta" role="alert">
                        {error}
                    </p>
                )}
                {exito && (
                    <p className="perfil__exito" role="status">
                        {exito}
                    </p>
                )}
                {aviso && (
                    <p className="perfil__info" role="status">
                        {aviso}
                    </p>
                )}

                <div className="perfil__acciones">
                    <button
                        type="button"
                        className="boton boton--secundario"
                        onClick={() => {
                            setFormulario(datosDesde(usuario));
                            setErroresCampos({});
                            setError("");
                            setExito("");
                            setAviso("");
                        }}
                        disabled={guardando}
                    >
                        Descartar cambios
                    </button>
                    <button
                        type="submit"
                        className="boton boton--primario"
                        disabled={guardando}
                    >
                        {guardando ? "Guardando..." : "Guardar cambios"}
                    </button>
                </div>
            </form>
        </section>
    );
}
