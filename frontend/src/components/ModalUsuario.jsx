import React, { useState } from 'react';
import { usuarioService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

export const ModalUsuario = ({ isOpen, onClose, onSuccess }) => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [rol, setRol] = useState('Administrador');
  const [sede, setSede] = useState(user?.usr_sede || 'Bogotá');
  const [password, setPassword] = useState('Password123!');
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setIsSubmitting(true);

    try {
      const response = await usuarioService.crear({
        txt_nombre: nombre,
        txt_email: email,
        cmb_rol: rol,
        cmb_sede: sede,
        usr_password: password
      });

      // Limpiar formulario y notificar éxito al componente padre
      setNombre('');
      setEmail('');
      setRol('Administrador');
      setSede(user?.usr_sede || 'Bogotá');
      onSuccess(response.data.mensaje || t('usuarios.successCreated'));
      onClose();
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setErrorMessage(err.response.data.detail);
      } else {
        setErrorMessage(t('usuarios.errorDuplicate'));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" id="modal_usuario">
        <div className="card-header" style={{ marginBottom: '1rem' }}>
          <h3 className="card-title">{t('usuarios.modalTitle')}</h3>
          <button 
            type="button" 
            onClick={onClose}
            className="btn btn-secondary"
            style={{ padding: '0.2rem 0.6rem' }}
          >
            ✕
          </button>
        </div>

        {/* Mensaje en texto rojo según C.A.4 */}
        {errorMessage && (
          <div className="alert alert-red" style={{ color: 'var(--color-red)' }}>
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="txt_nombre">{t('usuarios.nameLabel')} *</label>
            <input
              id="txt_nombre"
              type="text"
              className="form-input"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              required
              placeholder={t('usuarios.namePlaceholder')}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="txt_email">{t('usuarios.emailLabel')} *</label>
            <input
              id="txt_email"
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              pattern="^[^@\s]+@docusol\.com$"
              title="El correo debe pertenecer al dominio corporativo @docusol.com"
              placeholder={t('usuarios.emailPlaceholder')}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="cmb_rol">{t('usuarios.roleLabel')} *</label>
            <select
              id="cmb_rol"
              className="form-select"
              value={rol}
              onChange={(e) => setRol(e.target.value)}
              required
            >
              <option value="Administrador">{t('roles.Administrador')}</option>
              <option value="Radicador">{t('roles.Radicador')}</option>
              <option value="Gestionador">{t('roles.Gestionador')}</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="cmb_sede">{t('usuarios.branchLabel')} *</label>
            <select id="cmb_sede" className="form-select" value={sede} onChange={(e) => setSede(e.target.value)} required>
              <option value="Bogotá">Bogotá</option>
              <option value="Medellín">Medellín</option>
              <option value="Cali">Cali</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="txt_password_usr">Contraseña Inicial</label>
            <input
              id="txt_password_usr"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password123!"
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
            <button 
              type="button" 
              onClick={onClose} 
              className="btn btn-secondary"
            >
              {t('common.cancel')}
            </button>
            <button
              id="btn_guardar_usuario"
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? t('usuarios.saving') : t('usuarios.saveBtn')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
