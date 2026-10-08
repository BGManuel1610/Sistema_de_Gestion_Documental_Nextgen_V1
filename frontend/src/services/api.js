import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || (
  typeof window !== 'undefined' && window.location.hostname
    ? `http://${window.location.hostname}:8000`
    : 'http://localhost:8000'
);

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Interceptor para agregar token JWT en cada solicitud
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para manejar sesión expirada o ausente: limpia credenciales
// y devuelve al usuario al selector de sede en vez de dejar un error 401 suelto.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        window.location.assign('/');
      }
    }
    return Promise.reject(error);
  }
);

// Endpoints Sprint 1 & Sprint 2
export const authService = {
  login: (user_email, user_password, sede) =>
    api.post('/api/auth/login', { user_email, user_password, sede }),
  getMe: () => api.get('/api/auth/me'),
};

export const usuarioService = {
  listar: () => api.get('/api/usuarios'),
  crear: (data) => api.post('/api/usuarios', data),
  registrar: (sede, data) => api.post(`/api/usuarios/registro/${sede}`, data),
};

export const radicadoService = {
  listar: (params) => api.get('/api/radicados', { params }),
  obtener: (rad_id) => api.get(`/api/radicados/${rad_id}`),
  crear: (data) => api.post('/api/radicados', data),
};

export const anexoService = {
  listar: (rad_id) => api.get(`/api/anexos/${rad_id}`),
  subir: (formData) =>
    api.post('/api/anexos/subir', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  obtenerUrlArchivo: (anx_id) => {
    const token = localStorage.getItem('token');
    return `${API_BASE_URL}/api/anexos/archivo/${anx_id}${token ? `?token=${encodeURIComponent(token)}` : ''}`;
  },
  obtenerUrlPorRadicado: (rad_id) => {
    const token = localStorage.getItem('token');
    return `${API_BASE_URL}/api/anexos/radicado/${rad_id}/archivo${token ? `?token=${encodeURIComponent(token)}` : ''}`;
  },
};

export const trasladoService = {
  trasladar: (data) => api.post('/api/traslados', data),
};

export const recepcionService = {
  pendientes: (params) => api.get('/api/recepcion/pendientes', { params }),
  enGestion: (params) => api.get('/api/recepcion/en_gestion', { params }),
  aceptar: (rad_id) => api.post(`/api/recepcion/aceptar/${rad_id}`),
};

export const cierreService = {
  obtenerDetalle: (rad_id) => api.get(`/api/cierre/${rad_id}`),
  finalizar: (formData) =>
    api.post('/api/cierre', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
};

export const auditoriaService = {
  consultar: (rad_codigo) =>
    api.get(`/api/auditoria/trazabilidad/${encodeURIComponent(rad_codigo)}`),
};

export const reporteService = {
  consultar: (params) => api.get('/api/reportes', { params }),
  exportarExcel: (params) =>
    api.get('/api/reportes/exportar-excel', { params, responseType: 'blob' }),
};

export const dashboardService = {
  vencimientos: () => api.get('/api/dashboard/vencimientos'),
};

export default api;
