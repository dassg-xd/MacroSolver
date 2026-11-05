
export interface DatosRegistro {
    correo: string;
    contrasena: string;
    nombre: string;
    sexo: "Masculino" | "Femenino";
    fecha_nacimiento: string;
    altura_cm: number;
    factor_actividad: number;
    nivel_entrenamiento: "principiante" | "intermedio" | "avanzado";
}

export interface DatosLogin {
    correo: string;
    contrasena: string;
}

export interface UsuarioPublico {
    id: number;
    correo: string;
    nombre: string;
    sexo: "Masculino" | "Femenino";
    fecha_nacimiento: string;
    altura_cm: number;
    factor_actividad: number;
    nivel_entrenamiento: "principiante" | "intermedio" | "avanzado";
    creado_en: string;
}

export interface DatosPerfil {
    nombre?: string;
    sexo?: UsuarioPublico["sexo"];
    fecha_nacimiento?: string;
    altura_cm?: number;
    factor_actividad?: number;
    nivel_entrenamiento?: UsuarioPublico["nivel_entrenamiento"];
}

export interface RespuestaAuth {
    access_token: string;
    token_type: "bearer";
    usuario: UsuarioPublico;
}
