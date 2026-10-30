import { useState, type SubmitEvent } from "react";
import logoMacroSolver from "../../assets/componente1.png";
import { mensajeDeError } from "../../api/mensajeError";
import { registrarUsuario } from "./services/authService";
import type { DatosRegistro } from "../../types/auth";
import "../../styles/AuthStyles.css";

type ErroresCampos = {
  sexo?: string;
  fecha_nacimiento?: string;
  altura_cm?: string;
};

const FACTORES_ACTIVIDAD = ["1.2", "1.375", "1.55", "1.725", "1.9"];

export default function Registro() {
  const [paso, setPaso] = useState<1 | 2>(1);
  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [mostrarContrasena, setMostrarContrasena] = useState(false);
  const [mostrarConfirmacion, setMostrarConfirmacion] = useState(false);

  const [sexo, setSexo] = useState<DatosRegistro["sexo"] | "">("");
  const [fechaNacimiento, setFechaNacimiento] = useState("");
  const [alturaCm, setAlturaCm] = useState("");
  const [factorActividad, setFactorActividad] = useState("1.375");
  const [nivelEntrenamiento, setNivelEntrenamiento] =
    useState<DatosRegistro["nivel_entrenamiento"]>("principiante");

  const [erroresCampos, setErroresCampos] = useState<ErroresCampos>({});
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [registroCompleto, setRegistroCompleto] = useState(false);

  const cumpleLongitud = contrasena.length >= 8;
  const cumpleLetra = /[a-zA-Z]/.test(contrasena);
  const cumpleNumero = /\d/.test(contrasena);
  const contrasenasCoinciden =
    confirmacion.length > 0 && contrasena === confirmacion;

  function continuar(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (paso === 1) {
      if (!nombre.trim()) {
        setError("Ingresa tu nombre.");
        return;
      }

      if (!cumpleLongitud || !cumpleLetra || !cumpleNumero) {
        setError("La contraseña todavía no cumple los requisitos.");
        return;
      }

      if (new TextEncoder().encode(contrasena).length > 72) {
        setError("La contraseña no puede superar 72 bytes en UTF-8.");
        return;
      }

      if (contrasena !== confirmacion) {
        setError("Las contraseñas no coinciden.");
        return;
      }

      setPaso(2);
      return;
    }

    const nuevosErrores: ErroresCampos = {};

    if (!sexo) {
      nuevosErrores.sexo = "Elige una opción.";
    }

    const fecha = fechaNacimiento
      ? new Date(`${fechaNacimiento}T00:00:00`)
      : null;

    if (!fecha || Number.isNaN(fecha.getTime()) || fecha >= new Date()) {
      nuevosErrores.fecha_nacimiento =
        "La fecha de nacimiento debe ser anterior a hoy.";
    }

    const altura = Number(alturaCm);
    if (
      !alturaCm ||
      !Number.isFinite(altura) ||
      altura < 100 ||
      altura > 250
    ) {
      nuevosErrores.altura_cm = "Escribe una altura entre 100 y 250 cm.";
    }

    setErroresCampos(nuevosErrores);

    if (Object.keys(nuevosErrores).length > 0) {
      setError("Revisa los campos marcados.");
      return;
    }

    if (!sexo || !fechaNacimiento || !FACTORES_ACTIVIDAD.includes(factorActividad)) {
      setError("Revisa los datos del formulario.");
      return;
    }

    const datos: DatosRegistro = {
      nombre: nombre.trim(),
      correo: correo.trim(),
      contrasena,
      sexo,
      fecha_nacimiento: fechaNacimiento,
      altura_cm: altura,
      factor_actividad: Number(factorActividad),
      nivel_entrenamiento: nivelEntrenamiento,
    };

    void enviarRegistro(datos);
  }

  async function enviarRegistro(datos: DatosRegistro) {
    setEnviando(true);
    setError("");

    try {
      await registrarUsuario(datos);
      setRegistroCompleto(true);
    } catch (errorRegistro: unknown) {
      setError(mensajeDeError(errorRegistro));
    } finally {
      setEnviando(false);
    }
  }

  function volverAlPasoUno() {
    setPaso(1);
    setError("");
    setErroresCampos({});
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
        </div>

        <small className="registro__nota">
          MacroSolver no sustituye la asesoría de un profesional de la salud.
        </small>
      </aside>

      <section className="registro__contenido">
        <form className="registro__tarjeta" onSubmit={continuar}>
          <div className="registro__progreso">
            <span>
              Paso {paso} de 2 ·{" "}
              {paso === 1 ? "Tu cuenta" : "Datos para el cálculo"}
            </span>
            <div className="registro__barras" aria-label={`Paso ${paso} de 2`}>
              <span className="activo" />
              <span className={paso === 2 ? "activo" : ""} />
            </div>
          </div>

          {registroCompleto ? (
            <div role="status">
              <h2>Cuenta creada</h2>
              <p>
                Tu registro se completó correctamente y tu sesión ya está
                iniciada.
              </p>
            </div>
          ) : (
            <>
              <h2>
                {paso === 1 ? "Crea tu cuenta" : "Datos para el cálculo"}
              </h2>

              {paso === 1 ? (
                <>
                  <p className="registro__login">
                    ¿Ya tienes una? <a href="/login">Inicia sesión</a>
                  </p>

                  <label htmlFor="nombre">Nombre</label>
                  <input
                    id="nombre"
                    name="nombre"
                    autoComplete="name"
                    maxLength={150}
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
                      aria-label={
                        mostrarContrasena
                          ? "Ocultar contraseña"
                          : "Mostrar contraseña"
                      }
                      onClick={() =>
                        setMostrarContrasena((visible) => !visible)
                      }
                    >
                      {mostrarContrasena ? "Ocultar" : "Ver"}
                    </button>
                  </div>

                  <p className="registro__ayuda">
                    La contraseña debe cumplir los requisitos de abajo.
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
                        mostrarConfirmacion
                          ? "Ocultar contraseña"
                          : "Mostrar contraseña"
                      }
                      onClick={() =>
                        setMostrarConfirmacion((visible) => !visible)
                      }
                    >
                      {mostrarConfirmacion ? "Ocultar" : "Ver"}
                    </button>
                  </div>

                  {confirmacion && !contrasenasCoinciden && (
                    <p className="registro__error">
                      Las contraseñas no coinciden.
                    </p>
                  )}

                  <button className="registro__continuar" type="submit">
                    Continuar
                  </button>
                  <p className="registro__pie">
                    En el siguiente paso te pediremos los datos para calcular
                    tu plan.
                  </p>
                </>
              ) : (
                <>
                  <p className="registro__pie registro__intro">
                    Con estos datos estimamos tu gasto calórico. Puedes
                    cambiarlos luego en Mi perfil.
                  </p>

                  {error && (
                    <p className="registro__alerta" role="alert">
                      {error}
                    </p>
                  )}

                  <label htmlFor="sexo">Sexo</label>
                  <select
                    id="sexo"
                    value={sexo}
                    aria-invalid={Boolean(erroresCampos.sexo)}
                    onChange={(event) => {
                      setSexo(event.target.value as typeof sexo);
                      setErroresCampos((actuales) => ({
                        ...actuales,
                        sexo: undefined,
                      }));
                    }}
                  >
                    <option value="">Elige una opción</option>
                    <option value="Masculino">Masculino</option>
                    <option value="Femenino">Femenino</option>
                  </select>
                  {erroresCampos.sexo && (
                    <p className="registro__error-campo" role="alert">
                      {erroresCampos.sexo}
                    </p>
                  )}

                  <div className="registro__fila">
                    <div>
                      <label htmlFor="fechaNacimiento">
                        Fecha de nacimiento
                      </label>
                      <input
                        id="fechaNacimiento"
                        type="date"
                        value={fechaNacimiento}
                        aria-invalid={Boolean(erroresCampos.fecha_nacimiento)}
                        onChange={(event) => {
                          setFechaNacimiento(event.target.value);
                          setErroresCampos((actuales) => ({
                            ...actuales,
                            fecha_nacimiento: undefined,
                          }));
                        }}
                      />
                      {erroresCampos.fecha_nacimiento && (
                        <p className="registro__error-campo" role="alert">
                          {erroresCampos.fecha_nacimiento}
                        </p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="alturaCm">Altura (cm)</label>
                      <input
                        id="alturaCm"
                        type="number"
                        min="100"
                        max="250"
                        step="0.1"
                        inputMode="decimal"
                        placeholder="Ej. 176"
                        value={alturaCm}
                        aria-invalid={Boolean(erroresCampos.altura_cm)}
                        onChange={(event) => {
                          setAlturaCm(event.target.value);
                          setErroresCampos((actuales) => ({
                            ...actuales,
                            altura_cm: undefined,
                          }));
                        }}
                      />
                      {erroresCampos.altura_cm && (
                        <p className="registro__error-campo" role="alert">
                          {erroresCampos.altura_cm}
                        </p>
                      )}
                    </div>
                  </div>

                  <label htmlFor="factorActividad">Nivel de actividad</label>
                  <select
                    id="factorActividad"
                    value={factorActividad}
                    onChange={(event) =>
                      setFactorActividad(event.target.value)
                    }
                  >
                    <option value="1.2">Sedentario · 1,2</option>
                    <option value="1.375">Ligero · 1,375</option>
                    <option value="1.55">Moderado · 1,55</option>
                    <option value="1.725">Activo · 1,725</option>
                    <option value="1.9">Muy activo · 1,9</option>
                  </select>

                  <label htmlFor="nivelEntrenamiento">
                    Nivel de entrenamiento
                  </label>
                  <select
                    id="nivelEntrenamiento"
                    value={nivelEntrenamiento}
                    onChange={(event) =>
                      setNivelEntrenamiento(
                        event.target
                          .value as DatosRegistro["nivel_entrenamiento"],
                      )
                    }
                  >
                    <option value="principiante">Principiante</option>
                    <option value="intermedio">Intermedio</option>
                    <option value="avanzado">Avanzado</option>
                  </select>

                  <div className="registro__acciones">
                    <button
                      className="registro__atras"
                      type="button"
                      onClick={volverAlPasoUno}
                      disabled={enviando}
                    >
                      Atrás
                    </button>
                    <button
                      className="registro__continuar"
                      type="submit"
                      disabled={enviando}
                    >
                      {enviando ? "Creando cuenta..." : "Crear cuenta"}
                    </button>
                  </div>
                </>
              )}

              {paso === 1 && error && (
                <p className="registro__error" role="alert">
                  {error}
                </p>
              )}
            </>
          )}
        </form>
      </section>
    </main>
  );
}