import React from 'react';
import { Link } from 'react-router-dom';
import { SEDES } from '../utils/sedes';
import { useLanguage } from '../contexts/LanguageContext';
import { LanguageSwitcher } from '../components/LanguageSwitcher';

export const SeleccionSede = () => {
  const { t } = useLanguage();

  return (
    <div className="sede-selector-page">
      <div style={{ position: 'fixed', top: '1rem', right: '1.5rem', zIndex: 50 }}>
        <LanguageSwitcher />
      </div>

      <section className="sede-selector-panel" aria-labelledby="sede-selector-title">
        <div className="sede-welcome-panel">
          <img className="sede-brand-image" src="/docusol-logo.png" alt="DocuSol - Soluciones en Documentación" />
          <div className="sede-welcome-copy">
            <p className="sede-eyebrow">{t('branchSelect.eyebrow')}</p>
            <h1>{t('branchSelect.welcome')}</h1>
            <p>{t('branchSelect.selectBranchDesc')}</p>
          </div>
          <div className="sede-panel-index" aria-hidden="true">DocuSol <span>01 / 03</span></div>
        </div>

        <div className="sede-choice-panel">
          <header className="sede-choice-header">
            <p className="sede-eyebrow">{t('branchSelect.institutionalAccess')}</p>
            <h2 id="sede-selector-title">{t('branchSelect.selectYourBranch')}</h2>
            <p>{t('branchSelect.continueCredentials')}</p>
          </header>

          <nav className="sede-choice-list" aria-label="Seleccionar sede">
            {SEDES.map((sede, index) => (
              <Link
                key={sede.slug}
                to={`/login/${sede.slug}`}
                className="sede-choice"
                style={{
                  '--branch-color': sede.color,
                  '--branch-hover': sede.colorHover,
                  '--branch-soft': sede.colorSoft,
                }}
              >
                <span className="sede-choice-number">0{index + 1}</span>
                <span className="sede-choice-name">{sede.nombre}</span>
                <span className="sede-choice-arrow" aria-hidden="true">→</span>
              </Link>
            ))}
          </nav>
        </div>
      </section>
    </div>
  );
};