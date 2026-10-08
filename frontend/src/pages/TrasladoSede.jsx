import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { radicadoService, trasladoService } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

export const TrasladoSede = () => {
  const { t } = useLanguage();
  const [searchParams] = useSearchParams();
  const radIdParam = searchParams.get('rad_id');
  const [radicados, setRadicados] = useState([]);
  const [selectedRadId, setSelectedRadId] = useState('');
  const [nuevaSede, setNuevaSede] = useState('Medellín');
  const [motivo, setMotivo] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    cargarRadicados();
  }, [radIdParam]);

  const cargarRadicados = async () => {
    try {
      const res = await radicadoService.listar();
      const activos = (res.data || []).filter((r) => r.rad_estado !== 'FINALIZADO');
      setRadicados(activos);
      if (activos.length > 0) {
        if (radIdParam && activos.some((r) => r.rad_id === parseInt(radIdParam, 10))) {
          setSelectedRadId(parseInt(radIdParam, 10));
        } else {
          setSelectedRadId(activos[0].rad_id);
        }
      } else {
        setSelectedRadId('');
      }
    } catch (err) {
      console.error("Error al cargar radicados:", err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    // C.A.2: txt_motivo_traslado obligatorio
    if (!motivo || !motivo.trim()) {
      setErrorMessage(t('traslados.errorReason'));
      return;
    }

    if (!selectedRadId) {
      setErrorMessage(t('traslados.selectFilingPlaceholder'));
      return;
    }

    setLoading(true);

    try {
      // C.A.3 & C.A.4: Llamar al endpoint de traslado
      const res = await trasladoService.trasladar({
        rad_id: parseInt(selectedRadId, 10),
        cmb_nueva_sede: nuevaSede,
        txt_motivo_traslado: motivo.trim()
      });

      // C.A.5: Ventana emergente verde con texto exacto
      setSuccessMessage(res.data.mensaje || t('traslados.successTransferred'));
      setMotivo('');
      cargarRadicados();
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setErrorMessage(err.response.data.detail);
      } else {
        setErrorMessage(t('traslados.errorGeneral'));
      }
    } finally {
      setLoading(false);
    }
  };

  const radicadoSeleccionado = radicados.find(r => r.rad_id === parseInt(selectedRadId, 10));

  return (
    <div id="frm_traslado_sede" className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="card-header">
        <div>
          <h2 className="card-title">{t('traslados.title')}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {t('traslados.module')}
          </p>
        </div>
      </div>

      {/* C.A.2: Alerta en rojo exacta */}
      {errorMessage && (
        <div className="alert alert-red">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-red)' }}>✕</button>
        </div>
      )}

      {/* C.A.5: Ventana/alerta emergente verde exacta */}
      {successMessage && (
        <div className="alert alert-green">
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-green)' }}>✕</button>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* C.A.1: Selección de radicado */}
        <div className="form-group">
          <label className="form-label" htmlFor="cmb_radicado_traslado">
            {t('traslados.selectFilingLabel')} *
          </label>
          <select
            id="cmb_radicado_traslado"
            className="form-select"
            value={selectedRadId}
            onChange={(e) => setSelectedRadId(e.target.value)}
          >
            {radicados.map((rad) => (
              <option key={rad.rad_id} value={rad.rad_id}>
                {rad.rad_codigo} — {rad.rad_asunto.substring(0, 35)}... ({t('traslados.currentBranch')}: {t(`branches.${rad.rad_sede_actual}`) || rad.rad_sede_actual} | {rad.rad_estado})
              </option>
            ))}
          </select>
        </div>

        {radicadoSeleccionado && (
          <div style={{ backgroundColor: '#f8fafc', padding: '1rem', borderRadius: '6px', marginBottom: '1.25rem', border: '1px solid var(--border-color)', fontSize: '0.875rem' }}>
            <p><strong>{t('radicacion.senderLabel')}:</strong> {radicadoSeleccionado.rad_remitente}</p>
            <p><strong>{t('traslados.currentBranch')}:</strong> {t(`branches.${radicadoSeleccionado.rad_sede_actual}`) || radicadoSeleccionado.rad_sede_actual}</p>
            <p><strong>{t('common.status')}:</strong> <span className="badge" style={{ backgroundColor: '#e2e8f0' }}>{radicadoSeleccionado.rad_estado}</span></p>
          </div>
        )}

        {/* C.A.1: Destino en cmb_nueva_sede */}
        <div className="form-group">
          <label className="form-label" htmlFor="cmb_nueva_sede">
            {t('traslados.newBranchLabel')} *
          </label>
          <select
            id="cmb_nueva_sede"
            className="form-select"
            value={nuevaSede}
            onChange={(e) => setNuevaSede(e.target.value)}
          >
            <option value="Bogotá">Bogotá</option>
            <option value="Medellín">Medellín</option>
            <option value="Cali">Cali</option>
          </select>
        </div>

        {/* C.A.2: txt_motivo_traslado obligatorio */}
        <div className="form-group">
          <label className="form-label" htmlFor="txt_motivo_traslado">
            {t('traslados.reasonLabel')} *
          </label>
          <textarea
            id="txt_motivo_traslado"
            rows="4"
            className="form-textarea"
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            placeholder={t('traslados.reasonPlaceholder')}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
          {/* C.A.3: btn_confirmar_traslado */}
          <button
            id="btn_confirmar_traslado"
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? t('traslados.transferring') : t('traslados.confirmBtn')}
          </button>
        </div>
      </form>
    </div>
  );
};
