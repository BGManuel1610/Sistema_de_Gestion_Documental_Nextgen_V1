import React, { useState } from 'react';
import { auditoriaService } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

export const AuditoriaTrazabilidad = () => {
  const { t } = useLanguage();
  const [codigoBusqueda, setCodigoBusqueda] = useState('');
  const [trazabilidad, setTrazabilidad] = useState(null);
  const [warningMessage, setWarningMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleConsultar = async (e) => {
    e.preventDefault();
    setWarningMessage('');
    setTrazabilidad(null);

    const codigo = codigoBusqueda.trim();
    if (!codigo) {
      setWarningMessage(t('auditoria.searchPlaceholder'));
      return;
    }

    setLoading(true);

    try {
      // C.A.2: Consulta de base de datos
      const res = await auditoriaService.consultar(codigo);
      // C.A.4: Renderizar cronológicamente
      setTrazabilidad(res.data);
    } catch (err) {
      // C.A.3: Alerta en amarillo con texto exacto si no existe
      if (err.response && err.response.status === 404) {
        setWarningMessage('El número de radicado ingresado no existe en el sistema.');
      } else {
        setWarningMessage(t('auditoria.errorNotFound'));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div id="frm_auditoria_trazabilidad">
      <div className="card-header">
        <div>
          <h2 className="card-title">{t('auditoria.title')}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {t('auditoria.module')}
          </p>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleConsultar} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          {/* C.A.1: txt_buscar_radicado */}
          <div className="form-group" style={{ flex: 1, minWidth: '260px', marginBottom: 0 }}>
            <label className="form-label" htmlFor="txt_buscar_radicado">
              {t('auditoria.searchLabel')}
            </label>
            <input
              id="txt_buscar_radicado"
              type="text"
              className="form-input"
              value={codigoBusqueda}
              onChange={(e) => setCodigoBusqueda(e.target.value)}
              placeholder={t('auditoria.searchPlaceholder')}
            />
          </div>

          {/* C.A.2: btn_consultar_traza */}
          <button
            id="btn_consultar_traza"
            type="submit"
            className="btn btn-primary"
            disabled={loading || !codigoBusqueda.trim()}
            style={{ minWidth: '160px' }}
          >
            {loading ? t('auditoria.consulting') : `🔍 ${t('auditoria.consultBtn')}`}
          </button>
        </form>
      </div>

      {/* C.A.3: Alerta en amarillo exacta */}
      {warningMessage && (
        <div className="alert alert-yellow">
          <span>⚠️ {warningMessage}</span>
          <button onClick={() => setWarningMessage('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-yellow)' }}>✕</button>
        </div>
      )}

      {/* C.A.4 & C.A.5: grid_linea_tiempo estrictamente de solo lectura */}
      {trazabilidad && (
        <div className="card">
          <div className="card-header">
            <div>
              <h3 style={{ color: 'var(--primary)', fontSize: '1.1rem' }}>
                {t('auditoria.timelineTitle')}: <strong>{trazabilidad.rad_codigo}</strong>
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                {t('auditoria.subject')}: {trazabilidad.rad_asunto} | {t('auditoria.currentStatus')}: <strong>{trazabilidad.rad_estado_actual}</strong>
              </p>
            </div>
            <span className="badge" style={{ backgroundColor: '#f1f5f9', color: '#475569' }}>
              🔒 Registros Inalterables (Solo Lectura)
            </span>
          </div>

          <div className="table-container">
            <table id="grid_linea_tiempo" className="data-table">
              <thead>
                <tr>
                  <th>{t('auditoria.colDateTime')}</th>
                  <th>{t('auditoria.colUser')}</th>
                  <th>{t('auditoria.colOrigin')}</th>
                  <th>{t('auditoria.colDest')}</th>
                  <th>{t('auditoria.colAction')}</th>
                  <th>{t('auditoria.colStatus')}</th>
                </tr>
              </thead>
              <tbody>
                {trazabilidad.linea_tiempo.map((item, idx) => (
                  <tr key={idx}>
                    <td style={{ whiteSpace: 'nowrap', fontWeight: 500 }}>{item.fecha_hora}</td>
                    <td style={{ fontWeight: 600 }}>{item.usuario}</td>
                    <td>{t(`branches.${item.sede_origen}`) || item.sede_origen}</td>
                    <td>{t(`branches.${item.sede_destino}`) || item.sede_destino}</td>
                    <td>{item.accion_realizada}</td>
                    <td>
                      <span className={`badge ${
                        item.estado === 'RADICADO' ? 'badge-radicado' :
                        item.estado === 'TRASLADADO' ? 'badge-trasladado' :
                        item.estado === 'ACEPTADO' ? 'badge-aceptado' : 'badge-finalizado'
                      }`}>
                        {item.estado}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
