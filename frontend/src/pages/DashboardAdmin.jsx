import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

export const DashboardAdmin = () => {
  const { user } = useAuth();
  const { t } = useLanguage();

  return (
    <div id="frm_dashboard_admin">
      <div className="card-header">
        <div>
          <h2 className="card-title" style={{ fontSize: '1.5rem' }}>{t('dashboardAdmin.title')}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            {t('dashboardAdmin.welcome', { name: user?.usr_nombre, branch: user?.usr_sede })}
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem', marginTop: '1.5rem' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>{t('dashboardAdmin.userManagementTitle')}</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              {t('dashboardAdmin.userManagementDesc')}
            </p>
          </div>
          <Link to="/usuarios-admin" className="btn btn-primary" style={{ marginTop: '1.5rem' }}>
            {t('dashboardAdmin.userManagementBtn')}
          </Link>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>{t('dashboardAdmin.auditTitle')}</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              {t('dashboardAdmin.auditDesc')}
            </p>
          </div>
          <Link to="/auditoria-trazabilidad" className="btn btn-primary" style={{ marginTop: '1.5rem' }}>
            {t('dashboardAdmin.auditBtn')}
          </Link>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>{t('dashboardAdmin.reportsTitle')}</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              {t('dashboardAdmin.reportsDesc')}
            </p>
          </div>
          <Link to="/reportes-parametrizados" className="btn btn-primary" style={{ marginTop: '1.5rem' }}>
            {t('dashboardAdmin.reportsBtn')}
          </Link>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', borderLeft: '4px solid var(--primary)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <h3 style={{ color: 'var(--primary)', margin: 0 }}>{t('dashboardAdmin.backupTitle')}</h3>
              <span className="badge badge-primary" style={{ fontSize: '0.75rem', background: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd' }}>
                🛡️ Respaldo
              </span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              {t('dashboardAdmin.backupDesc')}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem', flexWrap: 'wrap' }}>
            <Link to="/bandeja-recepcion" className="btn btn-primary" style={{ flex: 1, minWidth: '140px', textAlign: 'center' }}>
              📥 {t('dashboardAdmin.backupInboxBtn')}
            </Link>
            <Link to="/radicacion-entrada" className="btn btn-secondary" style={{ flex: 1, minWidth: '120px', textAlign: 'center' }}>
              ✍️ {t('dashboardAdmin.backupFilingBtn')}
            </Link>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>{t('dashboardAdmin.deadlinesTitle')}</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              {t('dashboardAdmin.deadlinesDesc')}
            </p>
          </div>
          <Link to="/dashboard-vencimientos" className="btn btn-primary" style={{ marginTop: '1.5rem' }}>
            {t('dashboardAdmin.deadlinesBtn')}
          </Link>
        </div>
      </div>
    </div>
  );
};

