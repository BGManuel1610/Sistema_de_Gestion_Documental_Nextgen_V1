import React, { useState } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import { usuarioService } from '../services/api';
import { obtenerSede } from '../utils/sedes';
import { useLanguage } from '../contexts/LanguageContext';

export const CrearCuentaSede = () => {
  const { t } = useLanguage();
  const { sede: sedeSlug } = useParams();
  const sede = obtenerSede(sedeSlug);
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [rol, setRol] = useState('Radicador');
  const [password, setPassword] = useState('Password123!');
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  if (!sede) return <Navigate to="/" replace />;

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');
    setLoading(true);

    try {
      const response = await usuarioService.registrar(sede.slug, {
        txt_nombre: nombre,
        txt_email: email,
        cmb_rol: rol,
        usr_password: password,
        admin_email: adminEmail,
        admin_password: adminPassword,
      });
      setSuccessMessage(response.data.mensaje || t('createAccount.successCreated'));
      setNombre('');
      setEmail('');
      setAdminEmail('');
      setAdminPassword('');
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || 'Error creating account.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card" style={{ maxWidth: '560px', margin: '2rem auto' }}>
      <div className="card-header">
        <div>
          <h2 className="card-title">{t('createAccount.title')} · {sede.nombre}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {sede.nombre} — {t('createAccount.branchAccess')}
          </p>
        </div>
      </div>

      {errorMessage && <div className="alert alert-red">{errorMessage}</div>}
      {successMessage && <div className="alert alert-green">{successMessage}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="registro_nombre">{t('createAccount.nameLabel')}</label>
          <input id="registro_nombre" className="form-input" value={nombre} onChange={(event) => setNombre(event.target.value)} required placeholder={t('createAccount.namePlaceholder')} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="registro_email">{t('createAccount.emailLabel')}</label>
          <input id="registro_email" type="email" className="form-input" value={email} onChange={(event) => setEmail(event.target.value)} required pattern="^[^@\s]+@docusol\.com$" title="El correo debe pertenecer al dominio corporativo @docusol.com" placeholder={t('createAccount.emailPlaceholder')} />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="registro_rol">{t('createAccount.roleLabel')}</label>
          <select id="registro_rol" className="form-select" value={rol} onChange={(event) => setRol(event.target.value)}>
            <option value="Administrador">{t('roles.Administrador')}</option>
            <option value="Gestionador">{t('roles.Gestionador')}</option>
            <option value="Radicador">{t('roles.Radicador')}</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="registro_password">{t('createAccount.passwordLabel')}</label>
          <input id="registro_password" type="password" className="form-input" value={password} onChange={(event) => setPassword(event.target.value)} required placeholder={t('createAccount.passwordPlaceholder')} />
        </div>

        <h3 style={{ margin: '1.5rem 0 1rem', fontSize: '1rem' }}>Admin Authorization — {sede.nombre}</h3>
        <div className="form-group">
          <label className="form-label" htmlFor="admin_email">Admin Email</label>
          <input id="admin_email" type="email" className="form-input" value={adminEmail} onChange={(event) => setAdminEmail(event.target.value)} required pattern="^[^@\s]+@docusol\.com$" title="El administradorDebe pertenecer al dominio corporativo @docusol.com" />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="admin_password">Admin Password</label>
          <input id="admin_password" type="password" className="form-input" value={adminPassword} onChange={(event) => setAdminPassword(event.target.value)} required />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', marginTop: '1.5rem' }}>
          <Link className="btn btn-secondary" to={`/login/${sede.slug}`}>{t('createAccount.backToLogin')}</Link>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? t('createAccount.submitting') : t('createAccount.submitBtn')}
          </button>
        </div>
      </form>
    </section>
  );
};