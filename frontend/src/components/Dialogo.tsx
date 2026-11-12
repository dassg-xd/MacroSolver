import { useEffect, useRef, type ReactNode } from "react";

import "../styles/Dialogo.css";

interface Props {
    tituloId: string;
    children: ReactNode;
    onClose: () => void;
    className?: string;
    returnFocusRef?: { readonly current: HTMLElement | null };
}

function administrarFoco(
    dialogo: HTMLDivElement,
    cerrar: () => void,
    returnFocusRef?: { readonly current: HTMLElement | null },
): () => void {
    const focoAnterior =
        returnFocusRef?.current ??
        (document.activeElement instanceof HTMLElement
            ? document.activeElement
            : null);

    dialogo.focus();

    function elementosEnfocables(): HTMLElement[] {
        return Array.from(
            dialogo.querySelectorAll<HTMLElement>(
                'a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])',
            ),
        ).filter((elemento) => elemento.getClientRects().length > 0);
    }

    function alPresionarTecla(evento: KeyboardEvent) {
        if (evento.key === "Escape") {
            evento.preventDefault();
            cerrar();
            return;
        }

        if (evento.key !== "Tab") {
            return;
        }

        const enfocables = elementosEnfocables();
        if (enfocables.length === 0) {
            evento.preventDefault();
            dialogo.focus();
            return;
        }

        const primero = enfocables[0];
        const ultimo = enfocables[enfocables.length - 1];
        const focoActual = document.activeElement;

        if (
            evento.shiftKey &&
            (focoActual === primero ||
                focoActual === dialogo ||
                !dialogo.contains(focoActual))
        ) {
            evento.preventDefault();
            ultimo.focus();
        } else if (
            !evento.shiftKey &&
            (focoActual === ultimo ||
                focoActual === dialogo ||
                !dialogo.contains(focoActual))
        ) {
            evento.preventDefault();
            primero.focus();
        }
    }

    document.addEventListener("keydown", alPresionarTecla);

    return () => {
        document.removeEventListener("keydown", alPresionarTecla);
        if (focoAnterior?.isConnected) {
            focoAnterior.focus();
        }
    };
}

export default function Dialogo({
    tituloId,
    children,
    onClose,
    className = "",
    returnFocusRef,
}: Props) {
    const dialogoRef = useRef<HTMLDivElement>(null);
    const cerrarRef = useRef(onClose);

    useEffect(() => {
        cerrarRef.current = onClose;
    }, [onClose]);

    useEffect(() => {
        const dialogo = dialogoRef.current;
        if (!dialogo) {
            return;
        }

        return administrarFoco(
            dialogo,
            () => cerrarRef.current(),
            returnFocusRef,
        );
    }, [returnFocusRef]);

    return (
        <div
            className="modal-fondo"
            role="presentation"
            onClick={(evento) => {
                if (evento.target === evento.currentTarget) {
                    cerrarRef.current();
                }
            }}
        >
            <div
                ref={dialogoRef}
                className={`modal${className ? ` ${className}` : ""}`}
                role="dialog"
                aria-modal="true"
                aria-labelledby={tituloId}
                tabIndex={-1}
            >
                {children}
            </div>
        </div>
    );
}
