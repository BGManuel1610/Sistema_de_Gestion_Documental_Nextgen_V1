import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LanguageProvider } from './contexts/LanguageContext';
import { Navbar } from './components/Navbar';
import { ProtectedRoute } from './components/ProtectedRoute';

// Páginas HU001 - HU010
import { Login } from './pages/Login';
import { DashboardAdmin } from './pages/DashboardAdmin';
import { UsuariosAdmin } from './pages/UsuariosAdmin';
import { RadicacionEntrada } from './pages/RadicacionEntrada';
import { CargarAnexos } from './pages/CargarAnexos';
import { TrasladoSede } from './pages/TrasladoSede';
import { BandejaRecepcion } from './pages/BandejaRecepcion';
import { CierreExpediente } from './pages/CierreExpediente';
import { AuditoriaTrazabilidad } from './pages/AuditoriaTrazabilidad';
import { ReportesParametrizados } from './pages/ReportesParametrizados';
import { DashboardVencimientos } from './pages/DashboardVencimientos';
import { SeleccionSede } from './pages/SeleccionSede';
import { CrearCuentaSede } from './pages/CrearCuentaSede';
import { COLORES_ROL, obtenerSede, obtenerSedePorNombre } from './utils/sedes';

const RootRedirect = () => {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated || !user) return <SeleccionSede />;
  if (user.usr_rol === 'Administrador') return <Navigate to="/dashboard-admin" replace />;
  if (user.usr_rol === 'Radicador') return <Navigate to="/radicacion-entrada" replace />;
  if (user.usr_rol === 'Gestionador') return <Navigate to="/bandeja-recepcion" replace />;
  return <Navigate to="/login" replace />;
};

const AppFrame = () => {
  const { user } = useAuth();
  const location = useLocation();
  const sedeSlug = location.pathname.match(/^\/(?:login|crear-cuenta)\/([^/]+)/)?.[1];
  const sede = sedeSlug ? obtenerSede(sedeSlug) : obtenerSedePorNombre(user?.usr_sede);
  const perfil = sedeSlug ? null : user?.usr_rol;
  const variablesTema = {
    '--primary': sede?.color || '#1768A8',
    '--primary-hover': sede?.colorHover || '#0F548B',
    '--primary-light': sede?.colorSoft || '#E9F3FA',
    '--role-accent': COLORES_ROL[perfil] || sede?.color || '#354A5F',
  };

  return (
    <div className={`app-container${user ? ' role-themed' : ''}`} style={variablesTema}>
      <Navbar />
      <main className="main-content">
        <Routes>
              {/* Ruta pública */}
              <Route path="/login" element={<Navigate to="/" replace />} />
              <Route path="/login/:sede" element={<Login />} />
              <Route path="/crear-cuenta/:sede" element={<CrearCuentaSede />} />
              <Route path="/" element={<RootRedirect />} />

              {/* HU-001 & Panel Admin */}
              <Route
                path="/dashboard-admin"
                element={
                  <ProtectedRoute allowedRoles={['Administrador']}>
                    <DashboardAdmin />
                  </ProtectedRoute>
                }
              />

              {/* HU-002: Gestión de Cuentas de Usuario y Roles */}
              <Route
                path="/usuarios-admin"
                element={
                  <ProtectedRoute allowedRoles={['Administrador']}>
                    <UsuariosAdmin />
                  </ProtectedRoute>
                }
              />

              {/* HU-003: Radicación de Documentos e Indización de Metadatos */}
              <Route
                path="/radicacion-entrada"
                element={
                  <ProtectedRoute allowedRoles={['Radicador', 'Administrador']}>
                    <RadicacionEntrada />
                  </ProtectedRoute>
                }
              />

              {/* HU-004: Carga y Asociación de Adjuntos Digitales */}
              <Route
                path="/cargar-anexos"
                element={
                  <ProtectedRoute allowedRoles={['Radicador', 'Administrador']}>
                    <CargarAnexos />
                  </ProtectedRoute>
                }
              />

              {/* HU-005: Reasignación y Traslado Inter-Sedes */}
              <Route
                path="/traslado-sede"
                element={
                  <ProtectedRoute allowedRoles={['Radicador', 'Gestionador', 'Administrador']}>
                    <TrasladoSede />
                  </ProtectedRoute>
                }
              />

              {/* HU-006: Recepción y Aceptación de Expedientes Trasladados */}
              <Route
                path="/bandeja-recepcion"
                element={
                  <ProtectedRoute allowedRoles={['Gestionador', 'Administrador']}>
                    <BandejaRecepcion />
                  </ProtectedRoute>
                }
              />

              {/* HU-007: Cierre y Finalización de Trámite Documental */}
              <Route
                path="/cierre-expediente"
                element={
                  <ProtectedRoute allowedRoles={['Gestionador', 'Administrador']}>
                    <CierreExpediente />
                  </ProtectedRoute>
                }
              />

              {/* HU-008: Consulta de Trazabilidad e Historial Inalterable */}
              <Route
                path="/auditoria-trazabilidad"
                element={
                  <ProtectedRoute allowedRoles={['Administrador']}>
                    <AuditoriaTrazabilidad />
                  </ProtectedRoute>
                }
              />

              {/* HU-009: Generación y Exportación de Reportes Parametrizados */}
              <Route
                path="/reportes-parametrizados"
                element={
                  <ProtectedRoute allowedRoles={['Administrador', 'Gestionador']}>
                    <ReportesParametrizados />
                  </ProtectedRoute>
                }
              />

              {/* HU-010: Dashboard de Alertas y Vencimientos Legales */}
              <Route
                path="/dashboard-vencimientos"
                element={
                  <ProtectedRoute allowedRoles={['Administrador', 'Gestionador']}>
                    <DashboardVencimientos />
                  </ProtectedRoute>
                }
              />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
};

export const App = () => (
  <LanguageProvider>
    <AuthProvider>
      <Router>
        <AppFrame />
      </Router>
    </AuthProvider>
  </LanguageProvider>
);

export default App;
