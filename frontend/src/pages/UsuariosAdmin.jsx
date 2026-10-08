import React, { useState, useEffect } from 'react';
import { usuarioService } from '../services/api';
import { ModalUsuario } from '../components/ModalUsuario';
import { useLanguage } from '../contexts/LanguageContext';

export const UsuariosAdmin = () => {
  const { t } = useLanguage();
  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  const cargarUsuarios = async () => {
    try {
      setLoading(true);
      const res = await usuarioService.listar();
      setUsuarios(res.data);
    } catch (err) {
      console.error("Error al cargar lista de usuarios:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarUsuarios();
  }, []);

  const handleSuccess = (msg) => {
    setSuccessMessage(msg);
    cargarUsuarios();
    setTimeout(() => {
      setSuccessMessage('');
    }, 5000);
  };

  return (
    <div id="frm_usuarios_admin">
      <div className="card-header">
        <div>
          <h2 className="card-title">{t('usuarios.title')}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {t('usuarios.module')}
          </p>
        </div>

        {/* C.A.1: btn_crear_usuario habilitado */}
        <button
          id="btn_crear_usuario"
          className="btn btn-primary"
          onClick={() => setIsModalOpen(true)}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          {t('usuarios.newUserBtn')}
        </button>
      </div>

      {/* C.A.5: Alerta verde con el mensaje exacto */}
      {successMessage && (
        <div className="alert alert-green">
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-green)' }}>✕</button>
        </div>
      )}

      {/* C.A.1: Cargar tbl_lista_usuarios */}
      <div className="table-container">
        <table id="tbl_lista_usuarios" className="data-table">
          <thead>
            <tr>
              <th>{t('usuarios.colId')}</th>
              <th>{t('usuarios.colName')}</th>
              <th>{t('usuarios.colEmail')}</th>
              <th>{t('usuarios.colRole')}</th>
              <th>{t('usuarios.colBranch')}</th>
              <th>{t('usuarios.colStatus')}</th>
              <th>{t('usuarios.colCreatedAt')}</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>{t('usuarios.loadingUsers')}</td>
              </tr>
            ) : usuarios.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>{t('usuarios.noUsers')}</td>
              </tr>
            ) : (
              usuarios.map((usr) => (
                <tr key={usr.usr_id}>
                  <td>{usr.usr_id}</td>
                  <td style={{ fontWeight: 600 }}>{usr.usr_nombre}</td>
                  <td>{usr.usr_email}</td>
                  <td>
                    <span className="badge" style={{ backgroundColor: '#e2e8f0', color: '#334155' }}>
                      {t(`roles.${usr.usr_rol}`) || usr.usr_rol}
                    </span>
                  </td>
                  <td>{t(`branches.${usr.usr_sede}`) || usr.usr_sede}</td>
                  <td>
                    <span className="badge badge-en-tiempo">
                      {usr.usr_estado === 'ACTIVO' ? t('common.active') : usr.usr_estado}
                    </span>
                  </td>
                  <td>{usr.usr_fecha_creacion ? new Date(usr.usr_fecha_creacion).toLocaleString() : t('common.na')}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal modal_usuario (C.A.2) */}
      <ModalUsuario
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleSuccess}
      />
    </div>
  );
};
