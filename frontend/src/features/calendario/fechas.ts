// Fechas en formato AAAA-MM-DD sin pasar por Date en UTC, para que un día no
// se corra al anterior en Colombia (UTC−5).

export const NOMBRES_MES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

export const NOMBRES_DIA = [
    "Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado",
];

export const INICIALES_DIA = ["DOM", "LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB"];

function dos(n: number): string {
    return String(n).padStart(2, "0");
}

export function hoyLocal(): string {
    const d = new Date();
    return `${d.getFullYear()}-${dos(d.getMonth() + 1)}-${dos(d.getDate())}`;
}

export function mesDe(fecha: string): string {
    return fecha.slice(0, 7);
}

export function moverMes(mes: string, delta: number): string {
    const [anio, numero] = mes.split("-").map(Number);
    const total = anio * 12 + (numero - 1) + delta;
    return `${Math.floor(total / 12)}-${dos((total % 12) + 1)}`;
}

/** 0 = domingo, como en la cuadrícula del calendario. */
export function diaSemana(fecha: string): number {
    const [anio, mes, dia] = fecha.split("-").map(Number);
    return new Date(anio, mes - 1, dia).getDay();
}

export function tituloMes(mes: string): string {
    const [anio, numero] = mes.split("-").map(Number);
    const nombre = NOMBRES_MES[numero - 1];
    return `${nombre.charAt(0).toUpperCase()}${nombre.slice(1)} ${anio}`;
}

export function tituloDia(fecha: string): string {
    const [, mes, dia] = fecha.split("-").map(Number);
    return `${NOMBRES_DIA[diaSemana(fecha)]} ${dia} de ${NOMBRES_MES[mes - 1]}`;
}

export function numeroDia(fecha: string): number {
    return Number(fecha.slice(8, 10));
}

export function formatoKcal(valor: number): string {
    return Math.round(valor).toLocaleString("es-CO");
}
