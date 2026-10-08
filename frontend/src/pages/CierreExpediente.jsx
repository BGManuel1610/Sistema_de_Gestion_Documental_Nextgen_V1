import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { radicadoService, cierreService } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';

export const CierreExpediente = () => {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const radIdParam = searchParams.get('rad_id');

  const [radicados, setRadicados] = useState([]);
  const [selectedRadId, setSelectedRadId] = useState(radIdParam || '');
  const [observacion, setObservacion] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [detalleCierre, setDetalleCierre] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    cargarRadicados();
  }, []);

  useEffect(() => {
    if (radIdParam) {
      setSelectedRadId(radIdParam);
    }
  }, [radIdParam]);

  useEffect(() => {
    if (selectedRadId) {
      cargarDetalle(selectedRadId);
    }
  }, [selectedRadId]);

  const cargarRadicados = async () => {
    try {
      const res = await radicadoService.listar();
      // El backend solo permite cerrar expedientes asignados al gestionador
      // (el administrador puede cerrar cualquiera). Listar los demais aqui
      // producia un 404 al seleccionar y dejaba la vista en blanco.
      const cerrables = (res.data || []).filter((r) => {
        if (r.rad_estado === 'FINALIZADO') return false;
        if (user && user.usr_rol === 'Administrador') return true;
        return r.rad_usuario_gestionador === user?.usr_id;
      });
      setRadicados(cerrables);
      if (cerrables.length > 0) {
        const porParam = cerrables.find((r) => r.rad_id === parseInt(radIdParam, 10));
        setSelectedRadId(porParam ? porParam.rad_id : cerrables[0].rad_id);
      } else {
        setSelectedRadId('');
        setDetalleCierre(null);
      }
    } catch (err) {
      console.error("Error al cargar lista de radicados:", err);
    }
  };

  const cargarDetalle = async (radId) => {
    setErrorMessage('');
    try {
      const res = await cierreService.obtenerDetalle(radId);
      setDetalleCierre(res.data);
      if (res.data.respuesta) {
        setObservacion(res.data.respuesta.res_observacion);
      } else {
        setObservacion('');
      }
    } catch (err) {
      setDetalleCierre(null);
      const detalle = err.response && err.response.data && err.response.data.detail;
      setErrorMessage(detalle || t('cierre.errorCargarDetalle') || 'No se pudo cargar el detalle del expediente.');
    }
  };

  const handleFileChange = (e) => {
    setErrorMessage('');
    const file = e.target.files[0];
    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setErrorMessage(t('cierre.errorRequired'));
      return;
    }

    setSelectedFile(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    // C.A.2: Validación estricta de file_respuesta y txt_observacion_cierre
    if (!selectedFile || !observacion || !observacion.trim()) {
      setErrorMessage(t('cierre.errorRequired'));
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append('rad_id', selectedRadId);
    formData.append('txt_observacion_cierre', observacion.trim());
    formData.append('file_respuesta', selectedFile);

    try {
      // C.A.3 y C.A.4: Guardar en tbl_respuestas y actualizar rad_estado = 'FINALIZADO'
      const res = await cierreService.finalizar(formData);

      // C.A.5: Mensaje exacto en verde
      setSuccessMessage(res.data.mensaje || t('cierre.successClosed'));
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      cargarDetalle(selectedRadId);
      cargarRadicados();
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setErrorMessage(err.response.data.detail);
      } else {
        setErrorMessage(t('cierre.errorRequired'));
      }
    } finally {
      setLoading(false);
    }
  };

  const esSoloLectura = detalleCierre?.es_solo_lectura || detalleCierre?.radicado?.rad_estado === 'FINALIZADO';

  return (
    <div id="frm_cierre_expediente" className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="card-header">
        <div>
          <h2 className="card-title">{t('cierre.title')}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {t('cierre.module')}
          </p>
        </div>
        {esSoloLectura && (
          <span className="badge badge-finalizado" style={{ fontSize: '0.85rem' }}>
            🔒 {t('common.status')}: FINALIZADO
          </span>
        )}
      </div>

      {/* C.A.2: Mensaje en rojo exacto */}
      {errorMessage && (
        <div className="alert alert-red">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-red)' }}>✕</button>
        </div>
      )}

      {radicados.length === 0 && (
        <div className="alert alert-yellow">
          <span>{t('cierre.noCerrables')}</span>
        </div>
      )}

      {/* C.A.5: Mensaje en verde exacto */}
      {successMessage && (
        <div className="alert alert-green">
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-green)' }}>✕</button>
        </div>
      )}

      <div className="form-group">
        <label className="form-label" htmlFor="cmb_radicado_cierre">
          {t('cierre.selectFilingLabel')}
        </label>
        <select
          id="cmb_radicado_cierre"
          className="form-select"
          value={selectedRadId}
          onChange={(e) => setSelectedRadId(e.target.value)}
        >
          {radicados.map((rad) => (
            <option key={rad.rad_id} value={rad.rad_id}>
              {rad.rad_codigo} — {rad.rad_asunto.substring(0, 35)} ({rad.rad_estado})
            </option>
          ))}
        </select>
      </div>

      {detalleCierre?.radicado && (
        <div style={{ backgroundColor: '#f8fafc', padding: '1rem', borderRadius: '6px', marginBottom: '1.5rem', border: '1px solid var(--border-color)', fontSize: '0.875rem' }}>
          <p><strong>{t('cierre.filingCode')}:</strong> {detalleCierre.radicado.rad_codigo}</p>
          <p><strong>{t('cierre.filingSender')}:</strong> {detalleCierre.radicado.rad_remitente}</p>
          <p><strong>{t('cierre.filingSubject')}:</strong> {detalleCierre.radicado.rad_asunto}</p>
          <p><strong>{t('traslados.currentBranch')}:</strong> {t(`branches.${detalleCierre.radicado.rad_sede_actual}`) || detalleCierre.radicado.rad_sede_actual}</p>
          <p><strong>{t('common.status')}:</strong> <span className={`badge ${esSoloLectura ? 'badge-finalizado' : 'badge-aceptado'}`}>{detalleCierre.radicado.rad_estado}</span></p>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* C.A.1: file_respuesta para seleccionar PDF de respuesta */}
        <div className="form-group">
          <label className="form-label" htmlFor="file_respuesta">
            {t('cierre.responsePdfLabel')} *
          </label>
          <input
            id="file_respuesta"
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="form-input"
            onChange={handleFileChange}
            disabled={esSoloLectura}
          />
          {esSoloLectura && detalleCierre?.respuesta && (
            <small style={{ color: 'var(--color-green)', fontWeight: 500, display: 'block', marginTop: '0.25rem' }}>
              ✓ {t('cierre.responseRegistered')}
            </small>
          )}
        </div>

        {/* C.A.1: txt_observacion_cierre para registrar observaciones */}
        <div className="form-group">
          <label className="form-label" htmlFor="txt_observacion_cierre">
            {t('cierre.observationsLabel')} *
          </label>
          <textarea
            id="txt_observacion_cierre"
            rows="4"
            className="form-textarea"
            value={observacion}
            onChange={(e) => setObservacion(e.target.value)}
            disabled={esSoloLectura}
            placeholder={t('cierre.observationsPlaceholder')}
          />
        </div>

        {/* C.A.5: En modo solo lectura se deshabilita o bloquea la acción */}
        {!esSoloLectura ? (
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
            <button
              id="btn_finalizar_tramite"
              type="submit"
              className="btn btn-success"
              disabled={loading}
            >
              {loading ? t('cierre.finalizing') : t('cierre.finalizeBtn')}
            </button>
          </div>
        ) : (
          <div style={{ marginTop: '1.5rem', padding: '0.75rem', backgroundColor: '#f1f5f9', borderRadius: '6px', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Este trámite se encuentra cerrado. El registro no admite modificaciones ni eliminación según los Criterios de Aceptación.
          </div>
        )}
      </form>
    </div>
  );
};
