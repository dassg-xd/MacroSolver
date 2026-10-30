import { isAxiosError } from "axios";

const MENSAJE_INESPERADO =
    "Ocurrió un error inesperado al conectar con el servidor.";

function esObjeto(
    valor: unknown,
): valor is Record<string, unknown> {
    return typeof valor === "object" && valor !== null;
}

export function mensajeDeError(error: unknown): string {
    if (!isAxiosError(error)) {
        return MENSAJE_INESPERADO;
    }

    const data: unknown = error.response?.data;
    if (!esObjeto(data)) {
        return MENSAJE_INESPERADO;
    }

    if (typeof data.detail === "string") {
        return data.detail;
    }

    if (Array.isArray(data.detail)) {
        const mensajes = data.detail
            .filter(
                (item): item is Record<string, unknown> =>
                    esObjeto(item) && typeof item.msg === "string",
            )
            .map((item) => item.msg as string);

        if (mensajes.length > 0) {
            return mensajes.join(" ");
        }
    }

    if (typeof data.error === "string") {
        return data.error;
    }

    return MENSAJE_INESPERADO;
}