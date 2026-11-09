import { clienteAxios } from "../../api";
import type {
    ActividadCatalogo,
    ActividadDia,
    ActividadRegistrada,
    Calendario,
} from "../../types/registro";

export const obtenerCalendario = async (mes: string): Promise<Calendario> => {
    const response = await clienteAxios.get<Calendario>("/plans/active/calendario", {
        params: { mes },
    });
    return response.data;
};

export const obtenerCatalogoActividades = async (): Promise<ActividadCatalogo[]> => {
    const response = await clienteAxios.get<ActividadCatalogo[]>("/actividades");
    return response.data;
};

/** kcal = null borra el registro del día. */
export const guardarCalorias = async (fecha: string, kcal: number | null) => {
    const response = await clienteAxios.put<{ fecha: string; kcal: number | null }>(
        "/plans/active/calorias",
        { fecha, kcal },
    );
    return response.data;
};

/** peso_kg = null borra el registro del día. */
export const guardarPeso = async (fecha: string, peso_kg: number | null) => {
    const response = await clienteAxios.put<{ fecha: string; peso_kg: number | null }>(
        "/plans/active/pesos",
        { fecha, peso_kg },
    );
    return response.data;
};

/** Reemplaza todas las actividades del día; una lista vacía lo deja como descanso. */
export const guardarActividades = async (fecha: string, actividades: ActividadDia[]) => {
    const response = await clienteAxios.put<{
        fecha: string;
        actividades: ActividadRegistrada[];
        kcal_ejercicio: number;
    }>("/plans/active/actividades", { fecha, actividades });
    return response.data;
};
