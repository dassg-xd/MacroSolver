import { isAxiosError } from "axios";

import { clienteAxios } from "../../api";
import type {
    DatosPlan,
    VistaPreviaPlan,
    PlanActivo,
    CalculoPlan,
} from "../../types/plan";

export const estimarComposicion = async (data: {
    peso_kg: number;
    cuello_cm?: number;
    cintura_cm?: number;
    cadera_cm?: number;
}) => {
    const response = await clienteAxios.post("/plans/estimar-composicion", data);
    return response.data;
};

export const vistaPreviaPlan = async (
    data: DatosPlan
): Promise<VistaPreviaPlan> => {
    const response = await clienteAxios.post<VistaPreviaPlan>(
        "/plans/preview",
        data
    );
    return response.data;
};

export const confirmarPlan = async (data: DatosPlan): Promise<PlanActivo> => {
    const response = await clienteAxios.post<PlanActivo>("/plans", data);
    return response.data;
};

export const obtenerPlanActivo = async (): Promise<PlanActivo | null> => {
    try {
        const response = await clienteAxios.get<PlanActivo>("/plans/active");
        return response.data;
    } catch (error: unknown) {
        if (isAxiosError(error) && error.response?.status === 404) {
            return null;
        }
        throw error;
    }
};

export const obtenerCalculoActivo = async (): Promise<CalculoPlan | null> => {
    try {
        const response = await clienteAxios.get<CalculoPlan>(
            "/plans/active/calculo"
        );
        return response.data;
    } catch (error: unknown) {
        if (isAxiosError(error) && error.response?.status === 404) {
            return null;
        }
        throw error;
    }
};
