import { useRef, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import logoMacroSolver from "../assets/componente1.png";
import Dialogo from "./Dialogo";
import { useSesion } from "../features/auth/SesionContext";
import "../styles/Layout.css";

export default function Layout() {
    const { usuario, cerrarSesion } = useSesion();
    const navegar = useNavigate();
    const [menuAbierto, setMenuAbierto] = useState(false);
    const [cerrandoSesion, setCerrandoSesion] = useState(false);
    const cuentaBotonRef = useRef<HTMLButtonElement>(null);

    const nombre = usuario?.nombre ?? "";

    function confirmarCierre() {
        cerrarSesion();
        setCerrandoSesion(false);
        setMenuAbierto(false);
        navegar("/login", {
            replace: true,
            state: { aviso: "Cerraste sesión correctamente." },
        });
    }

    return (
        <div className="app">
            <header className="barra">
                <NavLink className="barra__marca" to="/panel" aria-label="MacroSolver, panel">
                    <img src={logoMacroSolver} alt="MacroSolver" />
                </NavLink>

                <nav className="barra__nav" aria-label="Navegación principal">
                    <NavLink to="/panel" end>
                        Panel
                    </NavLink>
                    <NavLink to="/calendario">Calendario</NavLink>
                    <NavLink to="/estadisticas">Estadísticas</NavLink>
                    <NavLink to="/historial">Historial</NavLink>
                    <NavLink to="/guia">Guía</NavLink>
                    <NavLink to="/nuevo-plan">Nuevo plan</NavLink>
                </nav>

                <div
                    className="barra__cuenta"
                    onKeyDown={(evento) => {
                        if (evento.key === "Escape" && menuAbierto) {
                            setMenuAbierto(false);
                            cuentaBotonRef.current?.focus();
                        }
                    }}
                >
                    <button
                        ref={cuentaBotonRef}
                        type="button"
                        className="barra__chip"
                        aria-expanded={menuAbierto}
                        aria-controls="menu-cuenta"
                        aria-label={`Menú de cuenta${nombre ? ` de ${nombre}` : ""}`}
                        onClick={() => setMenuAbierto((abierto) => !abierto)}
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
                <Outlet />
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
