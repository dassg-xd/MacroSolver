import type { ReactNode } from "react";

import "../styles/Esqueleto.css";

interface EstadoProps {
    mensaje: string;
    children: ReactNode;
    className?: string;
}

interface PaginaProps {
    mensaje: string;
    tipo?: "pagina" | "autenticacion" | "panel";
}

export function EstadoEsqueleto({
    mensaje,
    children,
    className = "",
}: EstadoProps) {
    return (
        <section
            className={`esqueleto-estado ${className}`.trim()}
            role="status"
            aria-busy="true"
        >
            <span className="esqueleto-estado__mensaje">{mensaje}</span>
            <div className="esqueleto-estado__contenido" aria-hidden="true">
                {children}
            </div>
        </section>
    );
}

export function BloqueEsqueleto({ className = "" }: { className?: string }) {
    return <span className={`esqueleto-bloque ${className}`.trim()} />;
}

export function EsqueletoIndicadores({ cantidad = 4 }: { cantidad?: number }) {
    return (
        <div className="esqueleto__indicadores">
            {Array.from({ length: cantidad }, (_, indice) => (
                <div className="esqueleto__indicador" key={indice}>
                    <BloqueEsqueleto className="esqueleto__etiqueta" />
                    <BloqueEsqueleto className="esqueleto__valor" />
                    <BloqueEsqueleto className="esqueleto__linea esqueleto__linea--corta" />
                </div>
            ))}
        </div>
    );
}

export function EsqueletoTabla({
    filas = 4,
    columnas = 4,
}: {
    filas?: number;
    columnas?: number;
}) {
    return (
        <div className="esqueleto__tabla">
            {Array.from({ length: filas }, (_, fila) => (
                <div
                    className="esqueleto__fila"
                    key={fila}
                    style={{
                        gridTemplateColumns: `repeat(${columnas}, minmax(0, 1fr))`,
                    }}
                >
                    {Array.from({ length: columnas }, (_, columna) => (
                        <BloqueEsqueleto
                            className="esqueleto__celda"
                            key={columna}
                        />
                    ))}
                </div>
            ))}
        </div>
    );
}

export default function EsqueletoPagina({
    mensaje,
    tipo = "pagina",
}: PaginaProps) {
    if (tipo === "autenticacion") {
        return (
            <EstadoEsqueleto
                mensaje={mensaje}
                className="esqueleto-pagina esqueleto-pagina--autenticacion"
            >
                <div className="esqueleto__tarjeta esqueleto__formulario">
                    <BloqueEsqueleto className="esqueleto__titulo" />
                    <BloqueEsqueleto className="esqueleto__linea" />
                    {Array.from({ length: 4 }, (_, indice) => (
                        <BloqueEsqueleto
                            className="esqueleto__campo"
                            key={indice}
                        />
                    ))}
                    <BloqueEsqueleto className="esqueleto__boton" />
                </div>
            </EstadoEsqueleto>
        );
    }

    return (
        <EstadoEsqueleto
            mensaje={mensaje}
            className={`esqueleto-pagina esqueleto-pagina--${tipo}`}
        >
            <header className="esqueleto__cabecera">
                <BloqueEsqueleto className="esqueleto__titulo" />
                <BloqueEsqueleto className="esqueleto__linea esqueleto__linea--ancha" />
            </header>
            <EsqueletoIndicadores />
            <section className="esqueleto__tarjeta">
                <BloqueEsqueleto className="esqueleto__subtitulo" />
                <BloqueEsqueleto className="esqueleto__linea" />
                <BloqueEsqueleto className="esqueleto__grafica" />
            </section>
            {tipo === "panel" && (
                <div className="esqueleto__tarjetas">
                    <section className="esqueleto__tarjeta">
                        <BloqueEsqueleto className="esqueleto__subtitulo" />
                        <BloqueEsqueleto className="esqueleto__linea" />
                        <BloqueEsqueleto className="esqueleto__linea esqueleto__linea--corta" />
                    </section>
                    <section className="esqueleto__tarjeta">
                        <BloqueEsqueleto className="esqueleto__subtitulo" />
                        <BloqueEsqueleto className="esqueleto__linea" />
                        <BloqueEsqueleto className="esqueleto__linea esqueleto__linea--corta" />
                    </section>
                </div>
            )}
        </EstadoEsqueleto>
    );
}
