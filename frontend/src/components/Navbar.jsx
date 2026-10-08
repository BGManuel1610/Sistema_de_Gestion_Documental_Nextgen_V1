import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { LanguageSwitcher } from './LanguageSwitcher';

export const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  if (!isAuthenticated || !user) return null;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const rol = user.usr_rol;

  return (
    <nav className="navbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
        <NavLink to="/" className="navbar-brand">
          <img className="navbar-brand-logo" src="/docusol-logo.png" alt="DocuSol" />
          <span>DocuSol</span>
        </NavLink>

        <ul className="navbar-nav">
          {/* Vistas Administrador */}
          {rol === 'Administrador' && (
            <>
              <li><NavLink to="/dashboard-admin" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.dashboard')}</NavLink></li>
              <li><NavLink to="/usuarios-admin" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.users')}</NavLink></li>
              <li><NavLink to="/bandeja-recepcion" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.inboxAdmin') || 'Bandeja de Radicados / Gestión'}</NavLink></li>
              <li><NavLink to="/radicacion-entrada" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.filing')}</NavLink></li>
              <li><NavLink to="/auditoria-trazabilidad" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.audit')}</NavLink></li>
              <li><NavLink to="/reportes-parametrizados" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.reports')}</NavLink></li>
              <li><NavLink to="/dashboard-vencimientos" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.deadlines')}</NavLink></li>
            </>
          )}

          {/* Vistas Radicador */}
          {rol === 'Radicador' && (
            <>
              <li><NavLink to="/radicacion-entrada" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.filing')}</NavLink></li>
              <li><NavLink to="/cargar-anexos" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.attachments')}</NavLink></li>
              <li><NavLink to="/traslado-sede" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.transfers')}</NavLink></li>
            </>
          )}

          {/* Vistas Gestionador */}
          {rol === 'Gestionador' && (
            <>
              <li><NavLink to="/bandeja-recepcion" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.inbox')}</NavLink></li>
              <li><NavLink to="/traslado-sede" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.transfers')}</NavLink></li>
              <li><NavLink to="/cierre-expediente" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.closure')}</NavLink></li>
              <li><NavLink to="/dashboard-vencimientos" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.deadlines')}</NavLink></li>
              <li><NavLink to="/reportes-parametrizados" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{t('navbar.reports')}</NavLink></li>
            </>
          )}
        </ul>
      </div>

      <div className="navbar-user">
        <LanguageSwitcher />
        <span>{user.usr_nombre}</span>
        <span className="user-badge">{t(`roles.${user.usr_rol}`) || user.usr_rol} — {user.usr_sede}</span>
        <button onClick={handleLogout} className="btn btn-secondary" style={{ padding: '0.3rem 0.8rem', fontSize: '0.75rem' }}>
          {t('navbar.logout')}
        </button>
      </div>
    </nav>
  );
};
