import axios from 'axios';

export const EVENTO_SESION_EXPIRADA = 'macrosolver:sesion-expirada';

// Configuracion base de axios conectada con la URL del backend.
const axiosClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,
});

// Adjuntar JWT en cada peticion
axiosClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('auth_token');
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// La sesion se cierra sola solo cuando el token falla. Un 401 del login es
// una credencial incorrecta y debe mostrarse en el formulario, no como
// sesion expirada.
axiosClient.interceptors.response.use(
    (response) => response,
    (error) => {
        const status = error.response?.status;
        const url: string = error.config?.url ?? '';
        const esLogin = url.includes('/auth/login');

        if (status === 401 && !esLogin) {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_usuario');

            const detalle = error.response?.data?.detail;
            window.dispatchEvent(
                new CustomEvent(EVENTO_SESION_EXPIRADA, {
                    detail:
                        typeof detalle === 'string'
                            ? detalle
                            : 'Tu sesión expiró. Inicia sesión de nuevo.',
                })
            );
        }
        return Promise.reject(error);
    }
);

export default axiosClient;
