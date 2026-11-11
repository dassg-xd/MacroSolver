import type { MacrosPlan, VistaPreviaPlan } from "./plan";

export interface PesoReal {
    dia: number;
    fecha: string;
    peso_kg: number;
}

export interface Tendencia {
    c: number;
    a: number;
    r2: number;
    n: number;
    tasa_semanal_pct: number;
    curva: number[];
}

export interface Seguimiento {
    plan_id: number;
    fecha_inicio: string;
    fecha_meta: string;
    plazo_dias: number;
    dia_actual: number;
    peso_objetivo_kg: number;
    tolerancia_kg: number;
    dias: number[];
    curva_ideal: number[];
    curva_adherencia: number[];
    estimado: boolean[];
    curva_ejercicio: number[] | null;
    pesos: PesoReal[];
    tendencia: Tendencia | null;
    llegada: {
        dia: number | null;
        fecha: string | null;
        retraso_dias: number | null;
        mensaje: string;
    };
    desviacion: {
        delta_kg: number | null;
        delta_meta_kg: number | null;
        delta_modelo_kg: number | null;
        sugerir: boolean;
        motivo: string;
    };
    hoy: {
        fecha: string;
        dia_plan: number;
        dias_restantes: number;
        kcal: number | null;
        objetivo_kcal: number;
        ultimo_peso_kg: number;
        peso_ideal_kg: number;
    };
}

export interface ReplaneacionPrevia extends VistaPreviaPlan {
    replaneacion: {
        sugerida: boolean;
        motivo: string;
        dia_ultimo_peso: number;
        fecha_ultimo_peso: string;
        peso_real_kg: number;
        aviso_composicion: string | null;
        actual: {
            ingesta_kcal: number;
            macros: MacrosPlan;
            dias_restantes: number;
        };
    };
}

export interface SemanaEstadistica {
    inicio: string;
    fin: string;
    dias_registrados: number;
    dias_cumplidos: number;
    adherencia_pct: number | null;
    peso_promedio_kg: number | null;
    variacion_kg: number | null;
    sesiones: number;
    minutos: number;
    kcal_ejercicio: number;
    parcial: boolean;
}

export interface Estadisticas {
    plan_id: number;
    banda_cumplimiento: number;
    resumen: {
        dias_transcurridos: number;
        dias_registrados: number;
        dias_cumplidos: number;
        adherencia_pct: number | null;
        promedio_kcal: number | null;
        objetivo_kcal: number;
        peso_inicial_kg: number;
        peso_actual_kg: number;
        cambio_kg: number;
        sesiones: number;
        minutos: number;
    };
    semanas: SemanaEstadistica[];
}

export interface PlanHistorial {
    id: number;
    estado: string;
    plan_previo_id: number | null;
    fecha_inicio: string;
    fecha_meta: string;
    plazo_dias: number;
    peso_inicial_kg: number;
    peso_objetivo_kg: number;
    ingesta_kcal: number;
    ultimo_peso_kg: number | null;
    cambio_kg: number | null;
    creado_en: string;
}

export interface ComidaGuia {
    nombre: string;
    porcentaje: number;
    kcal: number;
    proteina_g: number;
    grasa_g: number;
    carbohidratos_g: number;
}

export interface Guia {
    comidas: number;
    ingesta_kcal: number;
    proteina_g: number;
    grasa_g: number;
    carbohidratos_g: number;
    reparto: ComidaGuia[];
    consejos: string[];
}
