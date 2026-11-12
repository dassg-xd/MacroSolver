import { Suspense, useRef, useState, type KeyboardEvent } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import logoMacroSolver from "../assets/componente1.png";
import EsqueletoPagina from "./Esqueleto";
import Dialogo from "./Dialogo";
import { useSesion } from "../features/auth/SesionContext";
import "../styles/Layout.css";

export default function Layout() {
    const { usuario, cerrarSesion } = useSesion();
    const navegar = useNavigate();
    const [menuAbierto, setMenuAbierto] = useState(false);
    const [navegacionAbierta, setNavegacionAbierta] = useState(false);
    const [cerrandoSesion, setCerrandoSesion] = useState(false);
    const cuentaBotonRef = useRef<HTMLButtonElement>(null);
    const navegacionBotonRef = useRef<HTMLButtonElement>(null);

    const nombre = usuario?.nombre ?? "";

    function confirmarCierre() {
        cerrarSesion();
        setCerrandoSesion(false);
        setMenuAbierto(false);
        setNavegacionAbierta(false);
        navegar("/login", {
            replace: true,
            state: { aviso: "Cerraste sesión correctamente." },
        });
    }

    function manejarEscape(evento: KeyboardEvent<HTMLElement>) {
        if (evento.key !== "Escape") return;
        if (navegacionAbierta) {
            setNavegacionAbierta(false);
            navegacionBotonRef.current?.focus();
        } else if (menuAbierto) {
            setMenuAbierto(false);
            cuentaBotonRef.current?.focus();
        }
    }

    return (
        <div className="app">
            <header className="barra" onKeyDown={manejarEscape}>
                <NavLink className="barra__marca" to="/panel" aria-label="MacroSolver, panel">
                    <img src={logoMacroSolver} alt="MacroSolver" />
                </NavLink>

                <button
                    ref={navegacionBotonRef}
                    type="button"
                    className="barra__toggle"
                    aria-expanded={navegacionAbierta}
                    aria-controls="navegacion-principal"
                    aria-label={
                        navegacionAbierta
                            ? "Cerrar menú de navegación"
                            : "Abrir menú de navegación"
                    }
                    onClick={() => {
                        setNavegacionAbierta((abierta) => !abierta);
                        setMenuAbierto(false);
                    }}
                >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                        {navegacionAbierta ? (
                            <path d="m6 6 12 12M18 6 6 18" />
                        ) : (
                            <path d="M4 6h16M4 12h16M4 18h16" />
                        )}
                    </svg>
                </button>

                <nav
                    id="navegacion-principal"
                    className={`barra__nav${navegacionAbierta ? " barra__nav--abierta" : ""}`}
                    aria-label="Navegación principal"
                >
                    <NavLink to="/panel" end onClick={() => setNavegacionAbierta(false)}>
                        Seguimiento
                    </NavLink>
                    <NavLink to="/calendario" onClick={() => setNavegacionAbierta(false)}>
                        Calendario
                    </NavLink>
                    <NavLink to="/estadisticas" onClick={() => setNavegacionAbierta(false)}>
                        Estadísticas
                    </NavLink>
                    <NavLink to="/historial" onClick={() => setNavegacionAbierta(false)}>
                        Historial
                    </NavLink>
                    <NavLink to="/guia" onClick={() => setNavegacionAbierta(false)}>
                        Guía
                    </NavLink>
                    <NavLink to="/nuevo-plan" onClick={() => setNavegacionAbierta(false)}>
                        Nuevo plan
                    </NavLink>
                </nav>

                <div className="barra__cuenta">
                    <button
                        ref={cuentaBotonRef}
                        type="button"
                        className="barra__chip"
                        aria-expanded={menuAbierto}
                        aria-controls="menu-cuenta"
                        aria-label={`Menú de cuenta${nombre ? ` de ${nombre}` : ""}`}
                        onClick={() => {
                            setMenuAbierto((abierto) => !abierto);
                            setNavegacionAbierta(false);
                        }}
                    >
                        <span className="barra__inicial" aria-hidden="true">
                            {nombre.charAt(0).toUpperCase()}
                        </span>
                        <span>{nombre}</span>
                    </button>

                    <nav
                        id="menu-cuenta"
                        className="barra__menu"
                        aria-label="Opciones de cuenta"
                        hidden={!menuAbierto}
                    >
                        <NavLink
                            to="/perfil"
                            onClick={() => setMenuAbierto(false)}
                        >
                            Mi perfil
                        </NavLink>
                        <button
                            type="button"
                            onClick={() => {
                                setMenuAbierto(false);
                                setCerrandoSesion(true);
                            }}
                        >
                            Cerrar sesión
                        </button>
                    </nav>
                </div>
            </header>

            <main className="app__contenido">
                <Suspense
                    fallback={
                        <EsqueletoPagina mensaje="Cargando la pantalla..." />
                    }
                >
                    <Outlet />
                </Suspense>
            </main>

            <footer className="app__pie">
                <p>
                    MacroSolver no sustituye la asesoría de un profesional de la
                    salud. Los cálculos son estimaciones.
                </p>
            </footer>

            {cerrandoSesion && (
                <Dialogo
                    tituloId="titulo-cerrar-sesion"
                    onClose={() => setCerrandoSesion(false)}
                    returnFocusRef={cuentaBotonRef}
                >
                    <h2 id="titulo-cerrar-sesion">¿Cerrar sesión?</h2>
                    <p>
                        Tendrás que volver a iniciar sesión para ver tu plan y
                        tus registros.
                    </p>
                    <div className="modal__acciones">
                        <button
                            type="button"
                            className="boton boton--secundario"
                            onClick={() => setCerrandoSesion(false)}
                        >
                            Cancelar
                        </button>
                        <button
                            type="button"
                            className="boton boton--peligro"
                            onClick={confirmarCierre}
                        >
                            Cerrar sesión
                        </button>
                    </div>
                </Dialogo>
            )}
        </div>
    );
}
