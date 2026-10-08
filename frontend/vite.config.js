import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Cargar variables de entorno desde el entorno o archivo .env
  const env = loadEnv(mode, process.cwd(), '');
  const port = parseInt(process.env.FRONTEND_PORT || env.FRONTEND_PORT || process.env.PORT || env.PORT || '3000', 10);

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: port,
      // strictPort: false permite que si el puerto configurado (ej. 3000) está ocupado en el host,
      // Vite salte automáticamente al siguiente puerto libre disponible (3001, etc.) sin fallar
      strictPort: false,
      // Los bind mounts de Docker sobre Windows no emiten eventos de watcher (inotify)
      // dentro del contenedor Linux, por lo que Vite sirve bundles obsoletos.
      // usePolling fuerza la detección de cambios en el código fuente montado.
      watch: {
        usePolling: true,
        interval: 500,
      },
    },
    preview: {
      host: '0.0.0.0',
      port: port,
      strictPort: false,
    },
  };
});
