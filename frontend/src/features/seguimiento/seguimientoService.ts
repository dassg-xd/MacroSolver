import { isAxiosError } from "axios";

import { clienteAxios } from "../../api";
import type { PlanActivo } from "../../types/plan";
import type {
    Estadisticas,
    Guia,
    PlanHistorial,
    ReplaneacionPrevia,
    Seguimiento,
} from "../../types/seguimiento";

/** true si el backend respondió 404: el usuario todavía no tiene plan activo. */
export function esSinPlan(error: unknown): boolean {
    return isAxiosError(error) && error.response?.status === 404;
}

export const obtenerSeguimiento = async (): Promise<Seguimiento> => {
    const response = await clienteAxios.get<Seguimiento>("/plans/active/seguimiento");
    return response.data;
};

/** Sin fecha se conserva la fecha meta del plan; con fecha se acepta la fecha viable. */
export const vistaPreviaReplaneacion = async (fechaMeta?: string): Promise<ReplaneacionPrevia> => {
    const response = await clienteAxios.post<ReplaneacionPrevia>(
        "/plans/active/replanear/preview",
        fechaMeta ? { fecha_meta: fechaMeta } : {},
    );
    return response.data;
};

export const replanear = async (fechaMeta?: string): Promise<PlanActivo> => {
    const response = await clienteAxios.post<PlanActivo>(
        "/plans/active/replanear",
        fechaMeta ? { fecha_meta: fechaMeta } : {},
    );
    return response.data;
};

export const obtenerEstadisticas = async (): Promise<Estadisticas> => {
    const response = await clienteAxios.get<Estadisticas>("/plans/active/estadisticas");
    return response.data;
};

export const obtenerHistorial = async (): Promise<PlanHistorial[]> => {
    const response = await clienteAxios.get<PlanHistorial[]>("/plans");
    return response.data;
};

export const obtenerGuia = async (comidas: number): Promise<Guia> => {
    const response = await clienteAxios.get<Guia>("/guias", { params: { comidas } });
    return response.data;
};
