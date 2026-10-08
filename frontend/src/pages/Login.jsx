import React, { useState } from 'react';
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { obtenerSede } from '../utils/sedes';

export const Login = () => {
  const { sede: sedeSlug } = useParams();
  const sede = obtenerSede(sedeSlug);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  // C.A.2: btn_connect se habilita únicamente cuando user_email y user_password contengan caracteres
  const isButtonEnabled = email.trim().length > 0 && password.trim().length > 0;

  if (!sede) return <Navigate to="/" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isButtonEnabled) return;

    setErrorMessage('');
    setLoading(true);

    try {
      // C.A.4: Consultar tbl_usuarios validando usr_email y usr_password_hash
      const usuario = await login(email, password, sede.nombre);

      // C.A.5: Redirección según rol
      if (usuario.usr_rol === 'Administrador') {
        navigate('/dashboard-admin');
      } else if (usuario.usr_rol === 'Radicador') {
        navigate('/radicacion-entrada');
      } else if (usuario.usr_rol === 'Gestionador') {
        navigate('/bandeja-recepcion');
      } else {
        navigate('/');
      }
    } catch (err) {
      // C.A.5 / C.A.6: Mensaje emergente en color rojo con el texto exacto
      if (err.response && err.response.data && err.response.data.detail) {
        setErrorMessage(err.response.data.detail);
      } else {
        setErrorMessage(t('login.errorCredentials'));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      minHeight: '100vh',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'var(--bg-main)',
      padding: '1.5rem',
      position: 'relative'
    }}>
      {/* Selector de idioma flotante en esquina superior */}
      <div style={{ position: 'absolute', top: '1.5rem', right: '1.5rem' }}>
        <LanguageSwitcher style={{ background: '#ffffff', color: '#1e293b', border: '1px solid #cbd5e1', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' }} />
      </div>

      <div className="card" style={{ maxWidth: '440px', width: '100%', padding: '2.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <img className="login-brand-image" src="/docusol-logo.png" alt="DocuSol" />
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '0.25rem' }}>
            {t('login.title')}
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b' }}>
            DocuSol · {t('login.branchAccess')} {sede.nombre}
          </p>
        </div>

        {/* Mensaje emergente en rojo con texto exacto (C.A.5) */}
        {errorMessage && (
          <div className="alert alert-red" style={{ marginBottom: '1.5rem' }}>
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Formulario frm_login (C.A.1) */}
        <form id="frm_login" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="user_email">
              {t('login.email')}
            </label>
            <input
              id="user_email"
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('login.emailPlaceholder')}
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="user_password">
              {t('login.password')}
            </label>
            {/* C.A.3: Enmascarar caracteres mostrando asteriscos */}
            <input
              id="user_password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>

          {/* C.A.1 & C.A.2: btn_connect */}
          <button
            id="btn_connect"
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '1rem', padding: '0.75rem' }}
            disabled={!isButtonEnabled || loading}
          >
            {loading ? t('login.validating') : t('login.connectButton')}
          </button>
        </form>

        <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid #e2e8f0', fontSize: '0.8rem', color: '#64748b', textAlign: 'center' }}>
          <p><strong>{t('login.demoAccounts')} {sede.nombre}:</strong></p>
          {sede.cuentas.map((cuenta) => (
            <p key={cuenta.email}>{t(`roles.${cuenta.rol}`) || cuenta.rol}: <code>{cuenta.email}</code></p>
          ))}
          <p style={{ marginTop: '0.25rem' }}>{t('login.demoPassword')} <code>Password123!</code></p>
          <p style={{ marginTop: '1rem' }}>
            <Link to="/">{t('login.changeBranch')}</Link>
          </p>
          <p>
            <Link to={`/crear-cuenta/${sede.slug}`}>{t('login.createAccount')} {sede.nombre}</Link>
          </p>
        </div>
      </div>
    </div>
  );
};
