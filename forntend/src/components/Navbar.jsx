import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import logo from '../assets/logo.png';
import './Navbar.css';

const LANGS = [
  { code: 'en', label: 'English', short: 'EN' },
  { code: 'hi', label: 'हिंदी',   short: 'HI' },
  { code: 'mr', label: 'मराठी',   short: 'MR' },
];

export default function Navbar() {
  const { lang, setLang, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const dropRef = useRef(null);
  const current = LANGS.find(l => l.code === lang);

  useEffect(() => {
    const handler = (e) => {
      if (dropRef.current && !dropRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <header className="mobile-navbar">
      {/* Left — Logo + Brand */}
      <div className="mobile-navbar__brand">
        <img src={logo} alt="KisanSetu" className="mobile-navbar__logo" />
        <span className="mobile-navbar__wordmark">{t('brand')}</span>
      </div>

      {/* Right — Lang toggle + Avatar */}
      <div className="mobile-navbar__actions">
        <div className="lang-toggle" ref={dropRef}>
          <button
            id="lang-toggle-btn"
            className="btn-pill"
            onClick={() => setOpen(o => !o)}
            aria-haspopup="listbox"
            aria-expanded={open}
          >
            <span className="material-symbols-outlined icon" style={{ fontSize: 13 }}>language</span>
            <span>{current.short}</span>
            <span className="material-symbols-outlined icon" style={{ fontSize: 12 }}>
              {open ? 'expand_less' : 'expand_more'}
            </span>
          </button>

          {open && (
            <ul className="lang-dropdown" role="listbox">
              {LANGS.map(l => (
                <li
                  key={l.code}
                  role="option"
                  aria-selected={l.code === lang}
                  id={`lang-${l.code}`}
                  className={`lang-dropdown__item${l.code === lang ? ' lang-dropdown__item--active' : ''}`}
                  onClick={() => { setLang(l.code); setOpen(false); }}
                >
                  {l.label}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mobile-navbar__avatar">
          <span className="material-symbols-outlined icon-fill" style={{ fontSize: 18, color: '#1b5e20' }}>account_circle</span>
        </div>
      </div>
    </header>
  );
}
