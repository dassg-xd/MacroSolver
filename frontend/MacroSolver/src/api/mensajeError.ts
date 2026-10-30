import { isAxiosError } from 'axios';

const MENSAJE_INESPERADO = 'Ocurrió un error inesperado al conectar con el servidor.';

export const mensajeDeError = (err: unknown): string => {
    if (isAxiosError<{ error?: string }>(err) && err.response?.data?.error) {
        return err.response.data.error;
    }
    return MENSAJE_INESPERADO;
};
