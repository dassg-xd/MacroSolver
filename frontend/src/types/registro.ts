export type EstadoDia = "registrado" | "estimado" | "futuro" | "fuera_del_plan";

export interface ActividadCatalogo {
    id: number;
    nombre: string;
    tipo: string;
    met: number;
}

export interface ActividadRegistrada {
    actividad_id: number;
    nombre: string;
    tipo: string;
    met: number;
    minutos: number;
    kcal_estimadas: number;
}

export interface DiaCalendario {
    fecha: string;
    dia_plan: number | null;
    estado: EstadoDia;
    kcal: number | null;
    peso_kg: number | null;
    actividades: ActividadRegistrada[];
    kcal_ejercicio: number;
    cumplido: boolean | null;
}

export interface Calendario {
    mes: string;
    hoy: string;
    plan_id: number;
    fecha_inicio: string;
    fecha_meta: string;
    ingesta_objetivo_kcal: number;
    banda_cumplimiento: number;
    dias: DiaCalendario[];
}

export interface ActividadDia {
    actividad_id: number;
    minutos: number;
}
