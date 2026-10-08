export const SEDES = [
  {
    slug: 'bogota',
    nombre: 'Bogotá',
    color: '#1768A8',
    colorHover: '#0F548B',
    colorSoft: '#E9F3FA',
    cuentas: [
      { rol: 'Administrador', email: 'admin@docusol.com' },
      { rol: 'Radicador', email: 'radicador.bogota@docusol.com' },
      { rol: 'Gestionador', email: 'gestionador.bogota@docusol.com' },
    ],
  },
  {
    slug: 'medellin',
    nombre: 'Medellín',
    color: '#0F766E',
    colorHover: '#0B5F58',
    colorSoft: '#E7F4F1',
    cuentas: [
      { rol: 'Administrador', email: 'admin.medellin@docusol.com' },
      { rol: 'Radicador', email: 'radicador.medellin@docusol.com' },
      { rol: 'Gestionador', email: 'gestionador.medellin@docusol.com' },
    ],
  },
  {
    slug: 'cali',
    nombre: 'Cali',
    color: '#A9512A',
    colorHover: '#893F20',
    colorSoft: '#F8EEE8',
    cuentas: [
      { rol: 'Administrador', email: 'admin.cali@docusol.com' },
      { rol: 'Radicador', email: 'radicador.cali@docusol.com' },
      { rol: 'Gestionador', email: 'gestionador.cali@docusol.com' },
    ],
  },
];

export const obtenerSede = (slug) => SEDES.find((sede) => sede.slug === slug);
export const obtenerSedePorNombre = (nombre) => SEDES.find((sede) => sede.nombre === nombre);

export const COLORES_ROL = {
  Administrador: '#354A5F',
  Radicador: '#A66A00',
  Gestionador: '#287452',
};