import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { recepcionService, anexoService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

export const BandejaRecepcion = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [pendientes, setPendientes] = useState([]);
  const [enGestion, setEnGestion] = useState([]);
  const [loading, setLoading] = useState(true);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const esAdmin = user?.usr_rol === 'Administrador';
  const [sedeFiltro, setSedeFiltro] = useState(esAdmin ? 'Todas' : (user?.usr_sede || ''));

  const cargarBandejas = async (filtro = sedeFiltro) => {
    try {
      setLoading(true);
      const params = esAdmin && filtro ? { sede: filtro } : undefined;
      const [resPendientes, resEnGestion] = await Promise.all([
        recepcionService.pendientes(params),
        recepcionService.enGestion(params),
      ]);
      setPendientes(resPendientes.data);
      setEnGestion(resEnGestion.data);
    } catch (err) {
      console.error("Error al cargar bandejas:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarBandejas(sedeFiltro);
  }, []);

  const handleVerAdjunto = async (radId, radCodigo) => {
    setSuccessMessage('');
    setErrorMessage('');
    try {
      const res = await anexoService.listar(radId);
      if (res.data && res.data.length > 0) {
        const url = anexoService.obtenerUrlArchivo(res.data[0].anx_id);
        window.open(url, '_blank');
      } else {
        setErrorMessage(
          `${t('recepcion.noAttachmentAlert') || 'El radicado no cuenta con documentos adjuntos digitalizados.'} (${radCodigo})`
        );
      }
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setErrorMessage(err.response.data.detail);
      } else {
        setErrorMessage(t('recepcion.errorAttachment') || 'Error al consultar o abrir el documento adjunto.');
      }
    }
  };

  // C.A.3: Al presionar btn_aceptar_radicado
  const handleAceptar = async (radId) => {
    setSuccessMessage('');
    setErrorMessage('');
    try {
      const res = await recepcionService.aceptar(radId);
      // C.A.5: Notificación emergente con el texto exacto
      setSuccessMessage(res.data.mensaje || t('recepcion.successAccepted'));
      // C.A.4: Pasa automáticamente a grid_en_gestion
      cargarBandejas(sedeFiltro);
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setErrorMessage(err.response.data.detail);
      } else {
        setErrorMessage(t('recepcion.errorGeneral'));
      }
    }
  };

  return (
    <div id="frm_bandeja_recepcion">
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <h2 className="card-title" style={{ margin: 0 }}>{t('recepcion.title')}</h2>
            {esAdmin && (
              <span className="badge badge-primary" style={{ background: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd', fontWeight: 600 }}>
                🛡️ {t('recepcion.operationalBackup') || 'Respaldo Operativo'}
              </span>
            )}
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            {t('recepcion.module')} — {t('common.branch')}: <strong>{t(`branches.${user?.usr_sede}`) || user?.usr_sede}</strong> | {t(`roles.${user?.usr_rol}`) || user?.usr_rol}: <strong>{user?.usr_nombre}</strong>
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {esAdmin && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <label htmlFor="select_filtro_sede" style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)' }}>
                {t('recepcion.branchFilter') || 'Sede:'}
              </label>
              <select
                id="select_filtro_sede"
                className="form-control"
                style={{ width: 'auto', padding: '0.35rem 0.75rem', fontSize: '0.85rem' }}
                value={sedeFiltro}
                onChange={(e) => {
                  const nuevaSede = e.target.value;
                  setSedeFiltro(nuevaSede);
                  cargarBandejas(nuevaSede);
                }}
              >
                <option value="Todas">{t('recepcion.allBranches') || 'Todas las Sedes'}</option>
                <option value="Bogotá">Bogotá</option>
                <option value="Medellín">Medellín</option>
                <option value="Cali">Cali</option>
              </select>
            </div>
          )}
          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.85rem', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
            onClick={() => navigate('/radicacion-entrada')}
          >
            ✍️ {t('recepcion.newFilingBtn') || 'Radicar Entrada'}
          </button>
        </div>
      </div>

      {/* C.A.5: Notificación emergente verde con texto exacto */}
      {successMessage && (
        <div className="alert alert-green">
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-green)' }}>✕</button>
        </div>
      )}

      {errorMessage && (
        <div className="alert alert-red">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-red)' }}>✕</button>
        </div>
      )}

      {/* C.A.1: grid_pendientes (rad_sede_actual = sede_usuario y rad_estado = 'TRASLADADO') */}
      <div className="card">
        <div className="card-header" style={{ borderBottom: 'none', paddingBottom: '0' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', color: '#b45309', fontWeight: 600 }}>
              📥 {t('recepcion.tabPending')}
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              Documentos derivados a su sede que requieren aceptación formal para iniciar gestión.
            </p>
          </div>
          <span className="badge badge-trasladado">
            {pendientes.length}
          </span>
        </div>

        <div className="table-container">
          <table id="grid_pendientes" className="data-table">
            <thead>
              <tr>
                <th>{t('recepcion.colCode')}</th>
                <th>{t('recepcion.colSender')}</th>
                <th>{t('recepcion.colSubject')}</th>
                <th>{t('recepcion.colType')}</th>
                <th>{t('recepcion.colOrigin')}</th>
                <th>{t('common.status')}</th>
                <th>{t('common.date')}</th>
                <th>{t('recepcion.colAction')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '1.5rem' }}>{t('common.loading')}</td>
                </tr>
              ) : pendientes.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
                    {t('recepcion.noPending')}
                  </td>
                </tr>
              ) : (
                pendientes.map((p) => (
                  <tr key={p.rad_id}>
                    <td>
                      <button
                        type="button"
                        id={`btn_codigo_rad_${p.rad_id}`}
                        onClick={() => handleVerAdjunto(p.rad_id, p.rad_codigo)}
                        title={t('recepcion.viewAttachmentTooltip')}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          padding: 0,
                          fontWeight: 600,
                          color: 'var(--primary)',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          textDecoration: 'underline',
                          fontFamily: 'inherit',
                          fontSize: 'inherit',
                        }}
                      >
                        📄 {p.rad_codigo}
                      </button>
                    </td>
                    <td>{p.rad_remitente}</td>
                    <td>{p.rad_asunto}</td>
                    <td>{p.rad_tipo_doc}</td>
                    <td>{t(`branches.${p.rad_sede_actual}`) || p.rad_sede_actual}</td>
                    <td>
                      <span className={`badge badge-${p.rad_estado.toLowerCase()}`}>{p.rad_estado}</span>
                    </td>
                    <td>{new Date(p.rad_fecha_creacion).toLocaleDateString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <button
                          type="button"
                          id={`btn_ver_pdf_${p.rad_id}`}
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                          onClick={() => handleVerAdjunto(p.rad_id, p.rad_codigo)}
                          title={t('recepcion.viewAttachmentTooltip')}
                        >
                          👁️ {t('recepcion.viewAttachmentBtn')}
                        </button>
                        <button
                          id="btn_aceptar_radicado"
                          className="btn btn-success"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                          onClick={() => handleAceptar(p.rad_id)}
                        >
                          ✓ {t('recepcion.acceptBtn')}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* C.A.4: grid_en_gestion (Bandeja de trabajo en gestión) */}
      <div className="card">
        <div className="card-header" style={{ borderBottom: 'none', paddingBottom: '0' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', color: 'var(--primary)', fontWeight: 600 }}>
              💼 {t('recepcion.tabInManagement')}
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              Expedientes bajo su custodia directa pendientes de respuesta y cierre definitivo.
            </p>
          </div>
          <span className="badge badge-aceptado">
            {enGestion.length}
          </span>
        </div>

        <div className="table-container">
          <table id="grid_en_gestion" className="data-table">
            <thead>
              <tr>
                <th>{t('recepcion.colCode')}</th>
                <th>{t('recepcion.colSender')}</th>
                <th>{t('recepcion.colSubject')}</th>
                <th>{t('recepcion.colType')}</th>
                <th>{t('recepcion.colDeadline')}</th>
                <th>{t('common.status')}</th>
                <th>{t('recepcion.colAction')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '1.5rem' }}>{t('common.loading')}</td>
                </tr>
              ) : enGestion.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
                    {t('recepcion.noInManagement')}
                  </td>
                </tr>
              ) : (
                enGestion.map((g) => (
                  <tr key={g.rad_id}>
                    <td>
                      <button
                        type="button"
                        id={`btn_codigo_gestion_${g.rad_id}`}
                        onClick={() => handleVerAdjunto(g.rad_id, g.rad_codigo)}
                        title={t('recepcion.viewAttachmentTooltip')}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          padding: 0,
                          fontWeight: 600,
                          color: 'var(--primary)',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          textDecoration: 'underline',
                          fontFamily: 'inherit',
                          fontSize: 'inherit',
                        }}
                      >
                        📄 {g.rad_codigo}
                      </button>
                    </td>
                    <td>{g.rad_remitente}</td>
                    <td>{g.rad_asunto}</td>
                    <td>{g.rad_tipo_doc}</td>
                    <td>{new Date(g.rad_fecha_limite).toLocaleString()}</td>
                    <td>
                      <span className="badge badge-aceptado">{g.rad_estado}</span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <button
                          type="button"
                          id={`btn_ver_pdf_gestion_${g.rad_id}`}
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                          onClick={() => handleVerAdjunto(g.rad_id, g.rad_codigo)}
                          title={t('recepcion.viewAttachmentTooltip')}
                        >
                          👁️ {t('recepcion.viewAttachmentBtn')}
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                          onClick={() => navigate(`/traslado-sede?rad_id=${g.rad_id}`)}
                          title={t('recepcion.transferBtn')}
                        >
                          🔄 {t('recepcion.transferBtn')}
                        </button>
                        <button
                          className="btn btn-primary"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                          onClick={() => navigate(`/cierre-expediente?rad_id=${g.rad_id}`)}
                        >
                          {t('vencimientos.closeBtn')}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
