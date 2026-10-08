import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations } from '../utils/translations';

const LanguageContext = createContext(null);

export const LanguageProvider = ({ children }) => {
  // Por requerimiento expreso, el frontend completo se muestra en INGLÉS ('en') por defecto
  const [language, setLanguageState] = useState(() => {
    return localStorage.getItem('docuSol_lang') || 'en';
  });

  const setLanguage = (lang) => {
    if (lang === 'en' || lang === 'es') {
      localStorage.setItem('docuSol_lang', lang);
      setLanguageState(lang);
    }
  };

  const toggleLanguage = () => {
    const nextLang = language === 'en' ? 'es' : 'en';
    setLanguage(nextLang);
  };

  const t = (path, params = {}) => {
    if (!path) return '';
    const keys = path.split('.');
    
    // Buscar primero en el idioma actual
    let current = translations[language];
    for (const key of keys) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        current = null;
        break;
      }
    }

    // Fallback al inglés si no se encuentra en el idioma actual
    if (current === null && language !== 'en') {
      let fallback = translations.en;
      for (const key of keys) {
        if (fallback && typeof fallback === 'object' && key in fallback) {
          fallback = fallback[key];
        } else {
          fallback = null;
          break;
        }
      }
      current = fallback;
    }

    if (current === null || current === undefined) {
      return path;
    }

    // Reemplazar parámetros si los hay (ej: {code}, {name})
    if (typeof current === 'string' && Object.keys(params).length > 0) {
      let interpolated = current;
      for (const [pKey, pVal] of Object.entries(params)) {
        interpolated = interpolated.replace(new RegExp(`\\{${pKey}\\}`, 'g'), String(pVal));
      }
      return interpolated;
    }

    return current;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
