import React, { useState } from 'react';
import { reporteService } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

export const ReportesParametrizados = () => {
  const { t } = useLanguage();
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');
  const [sede, setSede] = useState('Todas');
  const [estado, setEstado] = useState('Todos');
  const [resultados, setResultados] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleGenerarReporte = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    // C.A.2: Validación fecha_final < fecha_inicial
    if (fechaInicio && fechaFin && fechaFin < fechaInicio) {
      setErrorMessage(t('reportes.errorDateRange'));
      return;
    }

    setLoading(true);

    try {
      const params = {};
      if (fechaInicio) params.dtp_fecha_inicio = fechaInicio;
      if (fechaFin) params.dtp_fecha_fin = fechaFin;
      if (sede) params.cmb_filtro_sede = sede;
      if (estado) params.cmb_filtro_estado = estado;

      // C.A.3: Consulta SQL en tbl_radicados
      const res = await reporteService.consultar(params);
      setResultados(res.data);
      setHasSearched(true);
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setErrorMessage(err.response.data.detail);
      } else {
        setErrorMessage(t('reportes.errorGeneral'));
      }
    } finally {
      setLoading(false);
    }
  };

  // C.A.5: Exportar y descargar archivo .xlsx
  const handleExportarExcel = async () => {
    setErrorMessage('');
    setExporting(true);

    const params = {};
    if (fechaInicio) params.dtp_fecha_inicio = fechaInicio;
    if (fechaFin) params.dtp_fecha_fin = fechaFin;
    if (sede) params.cmb_filtro_sede = sede;
    if (estado) params.cmb_filtro_estado = estado;

    try {
      const res = await reporteService.exportarExcel(params);

      // El backend puede devolver errores JSON con responseType blob.
      const contentType = res.headers['content-type'] || '';
      if (contentType.includes('application/json')) {
        const texto = await res.data.text();
        let detalle = texto;
        try {
          detalle = JSON.parse(texto).detail || texto;
        } catch (_) { /* respuesta no JSON */ }
        setErrorMessage(detalle);
        return;
      }

      const nombreArchivo = t('reportes.defaultFileName');
      const url = URL.createObjectURL(new Blob([res.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }));
      const enlace = document.createElement('a');
      enlace.href = url;
      enlace.download = nombreArchivo;
      document.body.appendChild(enlace);
      enlace.click();
      document.body.removeChild(enlace);
      URL.revokeObjectURL(url);
    } catch (err) {
      let detalle = '';
      if (err.response && err.response.data instanceof Blob) {
        try {
          detalle = JSON.parse(await err.response.data.text()).detail || '';
        } catch (_) { /* sin cuerpo legible */ }
      } else if (err.response && err.response.data && err.response.data.detail) {
        detalle = err.response.data.detail;
      }
      setErrorMessage(detalle || t('reportes.errorExport'));
    } finally {
      setExporting(false);
    }
  };

  // C.A.4: btn_exportar_excel habilitado ÚNICAMENTE cuando grid_resultados_reporte contiene al menos un registro
  const isExportEnabled = resultados.length > 0;

  return (
    <div id="frm_reportes_parametrizados">
      <div className="card-header">
        <div>
          <h2 className="card-title">{t('reportes.title')}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {t('reportes.module')}
          </p>
        </div>

        {/* C.A.4 & C.A.5: btn_exportar_excel */}
        <button
          id="btn_exportar_excel"
          type="button"
          className="btn btn-success"
          disabled={!isExportEnabled || exporting}
          onClick={handleExportarExcel}
        >
          {exporting ? t('reportes.exporting') : `📊 ${t('reportes.exportBtn')}`}
        </button>
      </div>

      {/* C.A.2: Alerta roja con mensaje exacto */}
      {errorMessage && (
        <div className="alert alert-red">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-red)' }}>✕</button>
        </div>
      )}

      {/* Formulario de Parámetros de Filtro (C.A.1) */}
      <div className="card">
        <form onSubmit={handleGenerarReporte}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
            {/* C.A.1: dtp_fecha_inicio */}
            <div className="form-group">
              <label className="form-label" htmlFor="dtp_fecha_inicio">
                {t('reportes.filterStartDate')}
              </label>
              <input
                id="dtp_fecha_inicio"
                type="date"
                className="form-input"
                value={fechaInicio}
                onChange={(e) => setFechaInicio(e.target.value)}
              />
            </div>

            {/* C.A.1: dtp_fecha_fin */}
            <div className="form-group">
              <label className="form-label" htmlFor="dtp_fecha_fin">
                {t('reportes.filterEndDate')}
              </label>
              <input
                id="dtp_fecha_fin"
                type="date"
                className="form-input"
                value={fechaFin}
                onChange={(e) => setFechaFin(e.target.value)}
              />
            </div>

            {/* C.A.1: cmb_filtro_sede */}
            <div className="form-group">
              <label className="form-label" htmlFor="cmb_filtro_sede">
                {t('reportes.filterBranch')}
              </label>
              <select
                id="cmb_filtro_sede"
                className="form-select"
                value={sede}
                onChange={(e) => setSede(e.target.value)}
              >
                <option value="Todas">{t('reportes.allBranches')}</option>
                <option value="Bogotá">Bogotá</option>
                <option value="Medellín">Medellín</option>
                <option value="Cali">Cali</option>
              </select>
            </div>

            {/* C.A.1: cmb_filtro_estado */}
            <div className="form-group">
              <label className="form-label" htmlFor="cmb_filtro_estado">
                {t('reportes.filterStatus')}
              </label>
              <select
                id="cmb_filtro_estado"
                className="form-select"
                value={estado}
                onChange={(e) => setEstado(e.target.value)}
              >
                <option value="Todos">{t('reportes.allStatuses')}</option>
                <option value="RADICADO">RADICADO</option>
                <option value="TRASLADADO">TRASLADADO</option>
                <option value="ACEPTADO">ACEPTADO</option>
                <option value="FINALIZADO">FINALIZADO</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
            {/* C.A.2 & C.A.3: btn_generar_reporte */}
            <button
              id="btn_generar_reporte"
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? t('reportes.generating') : `⚡ ${t('reportes.generateBtn')}`}
            </button>
          </div>
        </form>
      </div>

      {/* C.A.3: grid_resultados_reporte */}
      <div className="card">
        <div className="card-header" style={{ borderBottom: 'none', paddingBottom: 0 }}>
          <h3 style={{ fontSize: '1.1rem', color: 'var(--primary)' }}>
            {t('common.search')} ({resultados.length})
          </h3>
        </div>

        <div className="table-container">
          <table id="grid_resultados_reporte" className="data-table">
            <thead>
              <tr>
                <th>{t('reportes.colCode')}</th>
                <th>{t('reportes.colSender')}</th>
                <th>{t('reportes.colSubject')}</th>
                <th>{t('reportes.colType')}</th>
                <th>{t('reportes.colDestination')}</th>
                <th>{t('reportes.colCurrent')}</th>
                <th>{t('reportes.colStatus')}</th>
                <th>{t('reportes.colFilingDate')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>{t('common.loading')}</td>
                </tr>
              ) : resultados.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    {hasSearched ? t('reportes.noResults') : '...'}
                  </td>
                </tr>
              ) : (
                resultados.map((r) => (
                  <tr key={r.rad_id}>
                    <td style={{ fontWeight: 600, color: 'var(--primary)' }}>{r.rad_codigo}</td>
                    <td>{r.rad_remitente}</td>
                    <td>{r.rad_asunto}</td>
                    <td>{r.rad_tipo_doc}</td>
                    <td>{t(`branches.${r.rad_sede_destino}`) || r.rad_sede_destino}</td>
                    <td>{t(`branches.${r.rad_sede_actual}`) || r.rad_sede_actual}</td>
                    <td>
                      <span className={`badge ${
                        r.rad_estado === 'RADICADO' ? 'badge-radicado' :
                        r.rad_estado === 'TRASLADADO' ? 'badge-trasladado' :
                        r.rad_estado === 'ACEPTADO' ? 'badge-aceptado' : 'badge-finalizado'
                      }`}>
                        {r.rad_estado}
                      </span>
                    </td>
                    <td>{new Date(r.rad_fecha_creacion).toLocaleDateString()}</td>
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
