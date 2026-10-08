import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Cargando sesión...</div>;
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.usr_rol)) {
    // Redirigir al inicio correspondiente a su rol
    if (user.usr_rol === 'Administrador') return <Navigate to="/dashboard-admin" replace />;
    if (user.usr_rol === 'Radicador') return <Navigate to="/radicacion-entrada" replace />;
    if (user.usr_rol === 'Gestionador') return <Navigate to="/bandeja-recepcion" replace />;
    return <Navigate to="/login" replace />;
  }

  return children;
};
