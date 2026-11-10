export interface DatosPlan {
    peso_inicial_kg: number;
    peso_objetivo_kg: number;
    fecha_inicio?: string;
    fecha_meta: string;
    cuello_cm?: number;
    cintura_cm?: number;
    cadera_cm?: number;
}

export interface ComposicionPlan {
    pct_grasa: number;
    grasa_inicial_kg: number;
    masa_libre_inicial_kg: number;
    metodo: "marina" | "deurenberg";
    imc: number;
}

export interface ViabilidadPlan {
    viable: boolean;
    alcanzable: boolean;
    n_min_dias: number | null;
    fecha_viable: string | null;
    ingesta_rapida_kcal: number;
    ingesta_viable_kcal: number | null;
    mensaje: string;
}

export interface MacrosPlan {
    proteina_g: number;
    grasa_g: number;
    carbohidratos_g: number;
    fraccion_grasa: number;
    advertencia: string | null;
}

export interface CurvaPlan {
    dias: number[];
    peso_kg: number[];
    grasa_kg: number[];
    masa_libre_kg: number[];
    banda_inferior_kg: number[];
    banda_superior_kg: number[];
}

export interface PerdidaPlan {
    peso_kg: number;
    grasa_kg: number;
    masa_libre_kg: number;
}

export interface SensibilidadPlan {
    minimo_kcal: number;
    maximo_kcal: number;
    variantes: Record<string, number>;
    omitidas: string[];
}

export interface PasoSecante {
    k: number;
    ingesta_kcal: number;
    error_kg: number;
    paso: string;
}

export interface CalculoSecante {
    tolerancia_kg: number;
    max_iteraciones: number;
    raiz_kcal: number;
    error_raiz_kg: number;
    iteraciones: PasoSecante[];
}

export interface CalculoEuler {
    paso_dias: number;
    error_final_kg: number;
    error_maximo_kg: number;
}

export interface FormulasPlan {
    modelo: string;
    tdee: string;
    euler: string;
    secante: string;
    macros: string;
}

export interface CalculoPlan {
    secante: CalculoSecante;
    euler: CalculoEuler;
    sensibilidad: SensibilidadPlan | null;
    composicion: ComposicionPlan;
    viabilidad: ViabilidadPlan;
    formulas: FormulasPlan;
}

export interface BloqueoPlan {
    codigo: string;
    mensaje: string;
}

export interface VistaPreviaPlan {
    puede_confirmar: boolean;
    bloqueos: BloqueoPlan[];
    advertencias: string[];
    fecha_inicio: string;
    fecha_meta: string;
    plazo_dias: number;
    composicion: ComposicionPlan;
    viabilidad: ViabilidadPlan;
    ingesta_kcal: number | null;
    macros: MacrosPlan | null;
    curva: CurvaPlan | null;
    perdida: PerdidaPlan | null;
    sensibilidad: SensibilidadPlan | null;
    calculo: CalculoPlan | null;
}

export interface PlanActivo {
    id: number;
    fecha_inicio: string;
    fecha_meta: string;
    plazo_dias: number;
    peso_inicial_kg: number;
    peso_objetivo_kg: number;
    ingesta_kcal: number;
    proteina_g: number;
    grasa_g: number;
    carbohidratos_g: number;
    composicion: ComposicionPlan;
    tolerancia_kg: number;
    estado: string;
    creado_en: string;
    dias_transcurridos: number;
    dias_restantes: number;
}
