import { useEffect, useState } from "react";
import { CalendarDays, Check, RefreshCw, X } from "lucide-react";

import { mensajeDeError } from "../../api/mensajeError";
import {
    BloqueEsqueleto,
    EstadoEsqueleto,
    EsqueletoTabla,
} from "../../components/Esqueleto";
import Dialogo from "../../components/Dialogo";
import type { ReplaneacionPrevia } from "../../types/seguimiento";
import { conSigno, fechaCorta, num } from "../calendario/fechas";
import { replanear, vistaPreviaReplaneacion } from "./seguimientoService";

interface Props {
    onCerrar: () => void;
    onReplaneado: () => void;
}

type Carga =
    | { clave: string; tipo: "ok"; previa: ReplaneacionPrevia }
    | { clave: string; tipo: "error"; mensaje: string };

/** Propuesta de re-planeación: plan actual frente al nuevo. Nada cambia hasta confirmar. */
export default function Replaneacion({ onCerrar, onReplaneado }: Props) {
    const [fechaMeta, setFechaMeta] = useState<string | undefined>(undefined);
    const [carga, setCarga] = useState<Carga | null>(null);
    const [guardando, setGuardando] = useState(false);
    const [errorGuardar, setErrorGuardar] = useState<string | null>(null);

    const clave = fechaMeta ?? "plan";

    useEffect(() => {
        let vigente = true;
        vistaPreviaReplaneacion(fechaMeta)
            .then((previa) => {
                if (vigente) setCarga({ clave, tipo: "ok", previa });
            })
            .catch((error: unknown) => {
                if (vigente) setCarga({ clave, tipo: "error", mensaje: mensajeDeError(error) });
            });
        return () => {
            vigente = false;
        };
    }, [fechaMeta, clave]);

    async function confirmar() {
        setGuardando(true);
        setErrorGuardar(null);
        try {
            await replanear(fechaMeta);
            onReplaneado();
        } catch (error) {
            setErrorGuardar(mensajeDeError(error));
            setGuardando(false);
        }
    }

    const cargando = carga?.clave !== clave;
    const previa = carga?.tipo === "ok" ? carga.previa : null;
    const rep = previa?.replaneacion;

    return (
        <Dialogo
            className="replaneacion"
            tituloId="titulo-replaneacion"
            onClose={onCerrar}
        >
            <h2 id="titulo-replaneacion" className="replaneacion__titulo">
                <RefreshCw className="icono-ui" size={19} aria-hidden="true" />
                Re-planear
            </h2>

                {cargando && (
                    <EstadoEsqueleto
                        mensaje="Calculando la propuesta..."
                        className="replaneacion__carga"
                    >
                        <BloqueEsqueleto className="esqueleto__linea" />
                        <BloqueEsqueleto className="esqueleto__linea esqueleto__linea--ancha" />
                        <EsqueletoTabla filas={4} columnas={3} />
                    </EstadoEsqueleto>
                )}

                {!cargando && carga?.tipo === "error" && (
                    <p className="pagina__error" role="alert">
                        {carga.mensaje}
                    </p>
                )}

                {!cargando && previa && rep && (
                    <>
                        <p>
                            El plan nuevo parte de tu último peso,{" "}
                            <strong>{num(rep.peso_real_kg)} kg</strong> ({fechaCorta(rep.fecha_ultimo_peso)}),
                            y llega a la meta el <strong>{fechaCorta(previa.fecha_meta)}</strong>. El plan
                            actual queda guardado en el historial.
                        </p>

                        {previa.bloqueos.length > 0 && (
                            <div className="replaneacion__bloqueo">
                                {previa.bloqueos.map((b) => (
                                    <p key={b.codigo}>{b.mensaje}</p>
                                ))}
                                {previa.viabilidad.fecha_viable && (
                                    <button
                                        type="button"
                                        className="boton boton--secundario"
                                        onClick={() => setFechaMeta(previa.viabilidad.fecha_viable!)}
                                    >
                                        <CalendarDays size={16} aria-hidden="true" />
                                        Usar el {fechaCorta(previa.viabilidad.fecha_viable)} como nueva fecha
                                    </button>
                                )}
                            </div>
                        )}

                        {previa.puede_confirmar && previa.ingesta_kcal !== null && previa.macros && (
                            <table className="tabla replaneacion__tabla">
                                <thead>
                                    <tr>
                                        <th />
                                        <th>Plan actual</th>
                                        <th>Plan nuevo</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Ingesta</td>
                                        <td>{num(rep.actual.ingesta_kcal, 0)} kcal</td>
                                        <td>
                                            <strong>{num(previa.ingesta_kcal, 0)} kcal</strong>{" "}
                                            <small>
                                                ({conSigno(previa.ingesta_kcal - rep.actual.ingesta_kcal, 0)})
                                            </small>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>Proteína</td>
                                        <td>{num(rep.actual.macros.proteina_g, 0)} g</td>
                                        <td>{num(previa.macros.proteina_g, 0)} g</td>
                                    </tr>
                                    <tr>
                                        <td>Grasa</td>
                                        <td>{num(rep.actual.macros.grasa_g, 0)} g</td>
                                        <td>{num(previa.macros.grasa_g, 0)} g</td>
                                    </tr>
                                    <tr>
                                        <td>Carbohidratos</td>
                                        <td>{num(rep.actual.macros.carbohidratos_g, 0)} g</td>
                                        <td>{num(previa.macros.carbohidratos_g, 0)} g</td>
                                    </tr>
                                    <tr>
                                        <td>Días restantes</td>
                                        <td>{rep.actual.dias_restantes}</td>
                                        <td>{previa.plazo_dias}</td>
                                    </tr>
                                </tbody>
                            </table>
                        )}

                        {rep.aviso_composicion && <p className="tarjeta__nota">{rep.aviso_composicion}</p>}
                        {!rep.sugerida && previa.puede_confirmar && (
                            <p className="tarjeta__nota">
                                Ahora mismo no hace falta re-planear: {rep.motivo.toLowerCase()}
                            </p>
                        )}
                    </>
                )}

                {errorGuardar && (
                    <p className="pagina__error" role="alert">
                        {errorGuardar}
                    </p>
                )}

                <div className="modal__acciones">
                    <button type="button" className="boton boton--secundario" onClick={onCerrar}>
                        <X size={16} aria-hidden="true" />
                        Cancelar
                    </button>
                    <button
                        type="button"
                        className="boton boton--primario"
                        disabled={cargando || guardando || !previa?.puede_confirmar}
                        onClick={confirmar}
                    >
                        <Check size={16} aria-hidden="true" />
                        {guardando ? "Guardando..." : "Aceptar re-planeación"}
                    </button>
                </div>
        </Dialogo>
    );
}
