import { createContext, useCallback, useContext, useState } from 'react';
import en from '../locales/en.json';
import hi from '../locales/hi.json';
import mr from '../locales/mr.json';

const STORAGE_KEY = 'kisansetu_lang';
const locales = { en, hi, mr };
const SUPPORTED = Object.keys(locales);

function getSavedLang() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && SUPPORTED.includes(saved)) return saved;
  } catch { /* noop */ }
  return 'en';
}

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(getSavedLang);

  const setLang = useCallback((code) => {
    if (SUPPORTED.includes(code)) {
      setLangState(code);
      try { localStorage.setItem(STORAGE_KEY, code); } catch { /* noop */ }
    }
  }, []);

  const t = useCallback((key) => {
    const keys = key.split('.');
    let result = locales[lang];
    for (const k of keys) {
      result = result?.[k];
    }
    return result || key;
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
