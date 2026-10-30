import { useState, type SubmitEvent } from "react";
import logoMacroSolver from "../../assets/componente1.png";
import "../../styles/Registro.css";

interface DatosCuenta {
  nombre: string;
  correo: string;
  contrasena: string;
}

interface RegistroProps {
  onContinuar: (datos: DatosCuenta) => void;
}

export default function Registro({ onContinuar }: RegistroProps) {
  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [mostrarContrasena, setMostrarContrasena] = useState(false);
  const [mostrarConfirmacion, setMostrarConfirmacion] = useState(false);
  const [error, setError] = useState("");

  const cumpleLongitud = contrasena.length >= 8;
  const cumpleLetra = /[a-zA-Z]/.test(contrasena);
  const cumpleNumero = /\d/.test(contrasena);
  const contrasenasCoinciden =
    confirmacion.length > 0 && contrasena === confirmacion;

  function continuar(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!cumpleLongitud || !cumpleLetra || !cumpleNumero) {
      setError("La contraseña todavía no cumple los requisitos.");
      return;
    }

    if (contrasena !== confirmacion) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    onContinuar({ nombre: nombre.trim(), correo: correo.trim(), contrasena });
  }

  return (
    <main className="registro">
      <aside className="registro__panel">
        <a className="registro__marca" href="/" aria-label="MacroSolver, inicio">
            <img src={logoMacroSolver} alt="MacroSolver" />
        </a>

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
            Registra tu peso y lo que comes cada día. MacroSolver ajusta tu plan
            sobre la marcha para que sigas avanzando hacia tu meta.
          </p>

          <svg
            className="registro__grafica"
            viewBox="0 0 250 70"
            role="img"
            aria-label="Gráfica de progreso descendente"
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
          MacroSolver no sustituye la asesoría de un profesional de la salud.
        </small>
      </aside>

      <section className="registro__contenido">
        <form className="registro__tarjeta" onSubmit={continuar}>
          <div className="registro__progreso">
            <span>Paso 1 de 2 · Tu cuenta</span>
            <div className="registro__barras" aria-label="Paso 1 de 2">
              <span className="activo" />
              <span />
            </div>
          </div>

          <h2>Crea tu cuenta</h2>
          <p className="registro__login">
            ¿Ya tienes una? <a href="/login">Inicia sesión</a>
          </p>

          <label htmlFor="nombre">Nombre</label>
          <input
            id="nombre"
            name="nombre"
            autoComplete="name"
            placeholder="Tu nombre"
            value={nombre}
            onChange={(event) => setNombre(event.target.value)}
            required
          />

          <label htmlFor="correo">Correo</label>
          <input
            id="correo"
            name="correo"
            type="email"
            autoComplete="email"
            placeholder="usuario@correo.com"
            value={correo}
            onChange={(event) => setCorreo(event.target.value)}
            required
          />

          <label htmlFor="contrasena">Contraseña</label>
          <div className="registro__campo-contrasena">
            <input
              id="contrasena"
              name="contrasena"
              type={mostrarContrasena ? "text" : "password"}
              autoComplete="new-password"
              value={contrasena}
              onChange={(event) => setContrasena(event.target.value)}
              required
            />
            <button
              type="button"
              aria-label={mostrarContrasena ? "Ocultar contraseña" : "Mostrar contraseña"}
              onClick={() => setMostrarContrasena((visible) => !visible)}
            >
              {mostrarContrasena ? "Ocultar" : "Ver"}
            </button>
          </div>

          <p className="registro__ayuda">
            ⓘ La contraseña debe cumplir los requisitos de abajo.
          </p>

          <ul className="registro__requisitos">
            <li className={cumpleLongitud ? "cumplido" : ""}>
              {cumpleLongitud ? "✓" : "×"} Al menos 8 caracteres
            </li>
            <li className={cumpleLetra ? "cumplido" : ""}>
              {cumpleLetra ? "✓" : "×"} Al menos una letra
            </li>
            <li className={cumpleNumero ? "cumplido" : ""}>
              {cumpleNumero ? "✓" : "×"} Al menos un número
            </li>
          </ul>

          <label htmlFor="confirmacion">Confirma la contraseña</label>
          <div className="registro__campo-contrasena">
            <input
              id="confirmacion"
              name="confirmacion"
              type={mostrarConfirmacion ? "text" : "password"}
              autoComplete="new-password"
              placeholder="Escríbela de nuevo"
              value={confirmacion}
              onChange={(event) => setConfirmacion(event.target.value)}
              required
            />
            <button
              type="button"
              aria-label={
                mostrarConfirmacion ? "Ocultar contraseña" : "Mostrar contraseña"
              }
              onClick={() => setMostrarConfirmacion((visible) => !visible)}
            >
              {mostrarConfirmacion ? "Ocultar" : "Ver"}
            </button>
          </div>

          {confirmacion && !contrasenasCoinciden && (
            <p className="registro__error">Las contraseñas no coinciden.</p>
          )}
          {error && <p className="registro__error">{error}</p>}

          <button className="registro__continuar" type="submit">
            Continuar
          </button>

          <p className="registro__pie">
            En el siguiente paso te pediremos los datos para calcular tu plan.
          </p>
        </form>
      </section>
    </main>
  );
}