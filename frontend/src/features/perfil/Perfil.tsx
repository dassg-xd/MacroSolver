import { useState, type SubmitEvent } from "react";

import { mensajeDeError } from "../../api/mensajeError";
import type { DatosPerfil, UsuarioPublico } from "../../types/auth";
import { useSesion } from "../auth/SesionContext";
import "../../styles/Perfil.css";

const FACTORES = ["1.2", "1.375", "1.55", "1.725", "1.9"];

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
        setError("");
        setExito("");
    }

    async function enviar(event: SubmitEvent<HTMLFormElement>) {
        event.preventDefault();
        setError("");
        setExito("");

        const nombre = formulario.nombre.trim();
        const altura = Number(formulario.altura_cm);

        if (!nombre) {
            setError("Ingresa tu nombre.");
            return;
        }
        if (altura < 100 || altura > 250) {
            setError("Escribe una altura entre 100 y 250 cm.");
            return;
        }
        if (!formulario.fecha_nacimiento || edad === null || edad < 18) {
            setError("Debes tener al menos 18 años para usar MacroSolver.");
            return;
        }
        if (!FACTORES.includes(formulario.factor_actividad)) {
            setError("Elige un factor de actividad válido.");
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
            setExito("No hay cambios por guardar.");
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
                            value={formulario.nombre}
                            maxLength={150}
                            autoComplete="name"
                            onChange={(evento) =>
                                cambiar("nombre", evento.target.value)
                            }
                        />
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
                            type="date"
                            value={formulario.fecha_nacimiento}
                            onChange={(evento) =>
                                cambiar("fecha_nacimiento", evento.target.value)
                            }
                        />
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
                            type="number"
                            min="100"
                            max="250"
                            step="0.1"
                            inputMode="decimal"
                            value={formulario.altura_cm}
                            onChange={(evento) =>
                                cambiar("altura_cm", evento.target.value)
                            }
                        />
                    </div>
                    <div>
                        <label htmlFor="factorActividad">Nivel de actividad</label>
                        <select
                            id="factorActividad"
                            value={formulario.factor_actividad}
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

                <div className="perfil__acciones">
                    <button
                        type="button"
                        className="boton boton--secundario"
                        onClick={() => {
                            setFormulario(datosDesde(usuario));
                            setError("");
                            setExito("");
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
