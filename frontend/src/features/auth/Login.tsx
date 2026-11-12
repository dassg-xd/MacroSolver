import { useEffect, useRef, useState, type SubmitEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Eye, EyeOff, LogIn } from "lucide-react";

import logoMacroSolver from "../../assets/componente1.png";
import { mensajeDeError } from "../../api/mensajeError";
import { useSesion } from "./SesionContext";
import "../../styles/AuthStyles.css";

interface EstadoNavegacion {
    desde?: string;
    aviso?: string;
}

export default function Login() {
    const { iniciarSesion, avisoSesion, limpiarAviso } = useSesion();
    const navegar = useNavigate();
    const ubicacion = useLocation();
    const estado = ubicacion.state as EstadoNavegacion | null;

    const [correo, setCorreo] = useState("");
    const [contrasena, setContrasena] = useState("");
    const [mostrarContrasena, setMostrarContrasena] = useState(false);
    const [enviando, setEnviando] = useState(false);
    const [error, setError] = useState("");
    const errorRef = useRef<HTMLParagraphElement>(null);

    const aviso = estado?.aviso || avisoSesion;

    useEffect(() => {
        if (error) {
            errorRef.current?.focus();
        }
    }, [error]);

    async function enviarFormulario(event: SubmitEvent<HTMLFormElement>) {
        event.preventDefault();
        if (enviando) {
            return;
        }
        setError("");
        limpiarAviso();
        setEnviando(true);

        try {
            await iniciarSesion({
                correo: correo.trim(),
                contrasena,
            });

            const destino = estado?.desde || "/panel";
            navegar(destino, { replace: true });
        } catch (errorLogin: unknown) {
            setError(mensajeDeError(errorLogin));
        } finally {
            setEnviando(false);
        }
    }

    return (
        <main className="registro">
            <aside className="registro__panel">
                <Link className="registro__marca" to="/" aria-label="MacroSolver, inicio">
                    <img src={logoMacroSolver} alt="MacroSolver" />
                </Link>

                <div className="registro__mensaje">
                    <h1>
                        Pequeños
                        <br />
                        pasos diarios,
                        <br />
                        <span>un cambio</span>
                        <br />
                        <span>real.</span>
                    </h1>
                    <p>
                        Registra tu peso y lo que comes cada día. MacroSolver ajusta
                        tu plan sobre la marcha para que sigas avanzando hacia tu
                        meta.
                    </p>

                    <svg
                        className="registro__grafica"
                        viewBox="0 0 250 70"
                        aria-hidden="true"
                    >
                        <path
                            d="M5 10 35 17 58 14 78 24 99 26 120 37 140 35 158 45 179 49 201 59 225 63"
                            fill="none"
                            stroke="#e0242b"
                            strokeWidth="2"
                        />
                        <path
                            d="M5 13 35 20 58 18 78 27 99 30 120 40 140 39 158 48 179 52 201 61 225 65"
                            fill="none"
                            stroke="#777"
                            strokeDasharray="3 4"
                            strokeWidth="1"
                        />
                        <circle cx="225" cy="63" r="3" fill="#e0242b" />
                    </svg>
                </div>

                <small className="registro__nota">
                    MacroSolver no sustituye la asesoría de un profesional de la
                    salud.
                </small>
            </aside>

            <section className="registro__contenido">
                <form
                    className="registro__tarjeta login__tarjeta"
                    onSubmit={enviarFormulario}
                    aria-busy={enviando}
                >
                    <h2>Inicia sesión</h2>
                    <p className="registro__login">
                        Bienvenido de nuevo. ¿No tienes cuenta?{" "}
                        <Link to="/registro">Crea una</Link>
                    </p>

                    {aviso && !error && (
                        <p className="registro__aviso" role="status">
                            {aviso}
                        </p>
                    )}

                    <label htmlFor="correo">Correo</label>
                    <input
                        id="correo"
                        name="correo"
                        type="email"
                        autoComplete="email"
                        placeholder="nombre@correo.com"
                        value={correo}
                        onChange={(event) => {
                            setCorreo(event.target.value);
                            setError("");
                        }}
                        required
                    />

                    <label htmlFor="contrasena">Contraseña</label>
                    <div className="registro__campo-contrasena">
                        <input
                            id="contrasena"
                            name="contrasena"
                            type={mostrarContrasena ? "text" : "password"}
                            autoComplete="current-password"
                            placeholder="Tu contraseña"
                            value={contrasena}
                            onChange={(event) => {
                                setContrasena(event.target.value);
                                setError("");
                            }}
                            required
                        />
                        <button
                            type="button"
                            aria-label={
                                mostrarContrasena
                                    ? "Ocultar contraseña"
                                    : "Mostrar contraseña"
                            }
                            onClick={() =>
                                setMostrarContrasena((visible) => !visible)
                            }
                        >
                            {mostrarContrasena ? (
                                <EyeOff size={16} aria-hidden="true" />
                            ) : (
                                <Eye size={16} aria-hidden="true" />
                            )}
                        </button>
                    </div>

                    {error && (
                        <p
                            ref={errorRef}
                            id="login-error"
                            className="registro__alerta"
                            role="alert"
                            tabIndex={-1}
                        >
                            {error}
                        </p>
                    )}

                    <button
                        className="registro__continuar"
                        type="submit"
                        disabled={enviando}
                    >
                        <LogIn size={17} aria-hidden="true" />
                        {enviando ? "Iniciando sesión..." : "Iniciar sesión"}
                    </button>
                </form>
            </section>
        </main>
    );
}
