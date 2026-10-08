import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';

export const LanguageSwitcher = ({ style = {}, variant = 'default' }) => {
  const { language, setLanguage } = useLanguage();

  return (
    <div
      className={`language-switcher ${variant}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.25rem',
        background: 'rgba(255, 255, 255, 0.15)',
        border: '1px solid rgba(255, 255, 255, 0.25)',
        borderRadius: '20px',
        padding: '2px',
        backdropFilter: 'blur(4px)',
        fontSize: '0.75rem',
        fontWeight: 700,
        userSelect: 'none',
        ...style,
      }}
      title="Cambiar idioma / Change language"
    >
      <span style={{ padding: '0 4px', opacity: 0.8, display: 'flex', alignItems: 'center' }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="2" y1="12" x2="22" y2="12"></line>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
        </svg>
      </span>
      <button
        type="button"
        onClick={() => setLanguage('en')}
        style={{
          background: language === 'en' ? '#ffffff' : 'transparent',
          color: language === 'en' ? '#0f172a' : 'inherit',
          border: 'none',
          borderRadius: '16px',
          padding: '2px 8px',
          cursor: 'pointer',
          fontWeight: language === 'en' ? 800 : 500,
          transition: 'all 0.15s ease',
        }}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLanguage('es')}
        style={{
          background: language === 'es' ? '#ffffff' : 'transparent',
          color: language === 'es' ? '#0f172a' : 'inherit',
          border: 'none',
          borderRadius: '16px',
          padding: '2px 8px',
          cursor: 'pointer',
          fontWeight: language === 'es' ? 800 : 500,
          transition: 'all 0.15s ease',
        }}
      >
        ES
      </button>
    </div>
  );
};
