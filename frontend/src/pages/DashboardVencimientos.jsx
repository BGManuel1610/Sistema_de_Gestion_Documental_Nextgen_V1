import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { dashboardService } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

export const DashboardVencimientos = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('criticos'); // 'criticos', 'atencion', 'en_tiempo'

  useEffect(() => {
    cargarDashboard();
  }, []);

  const cargarDashboard = async () => {
    try {
      setLoading(true);
      const res = await dashboardService.vencimientos();
      setData(res.data);
    } catch (err) {
      console.error("Error al cargar dashboard de vencimientos:", err);
    } finally {
      setLoading(false);
    }
  };

  // C.A.5: Al hacer clic sobre cualquier registro de grid_criticos, redirigir a frm_cierre_expediente
  const handleFilaClick = (radId) => {
    navigate(`/cierre-expediente?rad_id=${radId}`);
  };

  return (
    <div id="frm_dashboard_vencimientos">
      <div className="card-header">
        <div>
          <h2 className="card-title">{t('vencimientos.title')}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {t('vencimientos.module')}
          </p>
        </div>
      </div>

      {/* Tarjetas KPI Semafóricas (C.A.2, C.A.3, C.A.4) */}
      <div className="kpi-grid">
        <div
          className="kpi-card"
          onClick={() => setActiveTab('criticos')}
          style={{
            cursor: 'pointer',
            borderLeft: '5px solid var(--color-red)',
            backgroundColor: activeTab === 'criticos' ? '#fff5f5' : 'white'
          }}
        >
          <span className="kpi-title" style={{ color: 'var(--color-red)' }}>🚨 {t('vencimientos.kpiCriticalSub')}</span>
          <span className="kpi-value" style={{ color: 'var(--color-red)' }}>{data?.total_criticos ?? 0}</span>
          <span className="badge badge-critico" style={{ marginTop: '0.5rem', alignSelf: 'flex-start' }}>{t('vencimientos.kpiCritical')}</span>
        </div>

        <div
          className="kpi-card"
          onClick={() => setActiveTab('atencion')}
          style={{
            cursor: 'pointer',
            borderLeft: '5px solid var(--color-yellow)',
            backgroundColor: activeTab === 'atencion' ? '#fffdf0' : 'white'
          }}
        >
          <span className="kpi-title" style={{ color: 'var(--color-yellow)' }}>⏳ {t('vencimientos.kpiAttentionSub')}</span>
          <span className="kpi-value" style={{ color: 'var(--color-yellow)' }}>{data?.total_atencion ?? 0}</span>
          <span className="badge badge-atencion" style={{ marginTop: '0.5rem', alignSelf: 'flex-start' }}>{t('vencimientos.kpiAttention')}</span>
        </div>

        <div
          className="kpi-card"
          onClick={() => setActiveTab('en_tiempo')}
          style={{
            cursor: 'pointer',
            borderLeft: '5px solid var(--color-green)',
            backgroundColor: activeTab === 'en_tiempo' ? '#f0fdf4' : 'white'
          }}
        >
          <span className="kpi-title" style={{ color: 'var(--color-green)' }}>✅ {t('vencimientos.kpiOnTimeSub')}</span>
          <span className="kpi-value" style={{ color: 'var(--color-green)' }}>{data?.total_en_tiempo ?? 0}</span>
          <span className="badge badge-en-tiempo" style={{ marginTop: '0.5rem', alignSelf: 'flex-start' }}>{t('vencimientos.kpiOnTime')}</span>
        </div>
      </div>

      {/* C.A.2: grid_criticos con etiqueta roja y estado CRÍTICO */}
      <div className="card">
        <div className="card-header" style={{ borderBottom: 'none', paddingBottom: '0.5rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', color: 'var(--primary)', fontWeight: 600 }}>
              {activeTab === 'criticos' && `🚨 ${t('vencimientos.kpiCritical')} (${t('vencimientos.kpiCriticalSub')})`}
              {activeTab === 'atencion' && `⏳ ${t('vencimientos.kpiAttention')} (${t('vencimientos.kpiAttentionSub')})`}
              {activeTab === 'en_tiempo' && `✅ ${t('vencimientos.kpiOnTime')} (${t('vencimientos.kpiOnTimeSub')})`}
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              {t('vencimientos.tableTitle')}
            </p>
          </div>
        </div>

        <div className="table-container">
          <table id="grid_criticos" className="data-table">
            <thead>
              <tr>
                <th>{t('vencimientos.colCode')}</th>
                <th>{t('recepcion.colSender')}</th>
                <th>{t('vencimientos.colSubject')}</th>
                <th>{t('vencimientos.colBranch')}</th>
                <th>{t('common.status')}</th>
                <th>{t('vencimientos.colDeadline')}</th>
                <th>{t('vencimientos.colRemaining')}</th>
                <th>{t('vencimientos.colSla')}</th>
                <th>{t('vencimientos.colAction')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '2rem' }}>{t('common.loading')}</td>
                </tr>
              ) : (
                (() => {
                  const lista = activeTab === 'criticos' ? data?.grid_criticos :
                                activeTab === 'atencion' ? data?.grid_atencion : data?.grid_en_tiempo;

                  if (!lista || lista.length === 0) {
                    return (
                      <tr>
                        <td colSpan="9" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                          {t('vencimientos.noCritical')}
                        </td>
                      </tr>
                    );
                  }

                  return lista.map((r) => (
                    <tr
                      key={r.rad_id}
                      onClick={() => handleFilaClick(r.rad_id)}
                      style={{ cursor: 'pointer' }}
                      title="Hacer clic para redirigir al formulario de cierre"
                    >
                      <td style={{ fontWeight: 700, color: 'var(--primary)' }}>{r.rad_codigo}</td>
                      <td>{r.rad_remitente}</td>
                      <td>{r.rad_asunto}</td>
                      <td>{t(`branches.${r.rad_sede_actual}`) || r.rad_sede_actual}</td>
                      <td>
                        <span className="badge" style={{ backgroundColor: '#e2e8f0' }}>{r.rad_estado}</span>
                      </td>
                      <td style={{ whiteSpace: 'nowrap' }}>{new Date(r.rad_fecha_limite).toLocaleString()}</td>
                      <td style={{ fontWeight: 600 }}>
                        {r.horas_restantes <= 0 ? (
                          <span style={{ color: 'var(--color-red)' }}>¡VENCIDO! ({r.horas_restantes}h)</span>
                        ) : (
                          `${r.horas_restantes} h`
                        )}
                      </td>
                      <td>
                        <span className={`badge ${
                          r.estado_semaforo === 'CRÍTICO' ? 'badge-critico' :
                          r.estado_semaforo === 'ATENCIÓN' ? 'badge-atencion' : 'badge-en-tiempo'
                        }`}>
                          {r.estado_semaforo === 'CRÍTICO' ? t('vencimientos.kpiCritical') :
                           r.estado_semaforo === 'ATENCIÓN' ? t('vencimientos.kpiAttention') : t('vencimientos.kpiOnTime')}
                        </span>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleFilaClick(r.rad_id);
                          }}
                        >
                          {t('vencimientos.closeBtn')} ➔
                        </button>
                      </td>
                    </tr>
                  ));
                })()
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
