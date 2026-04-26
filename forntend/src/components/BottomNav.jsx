import { NavLink } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import './BottomNav.css';

const NAV_ITEMS = [
  { to: '/',         icon: 'dashboard',   labelKey: 'nav.dashboard' },
  { to: '/fields',   icon: 'potted_plant',labelKey: 'nav.fields'    },
  { to: '/voice',    icon: 'mic',         labelKey: 'nav.voice'     },
  { to: '/analysis',  icon: 'eco',         labelKey: 'nav.analysis'  },
  { to: '/settings', icon: 'settings',    labelKey: 'nav.settings'  },
];

export default function BottomNav() {
  const { t } = useLanguage();

  return (
    <nav className="bottom-nav" aria-label="Bottom navigation">
      {NAV_ITEMS.map(({ to, icon, labelKey }) => (
        <NavLink
          key={to}
          to={to}
          id={`bottom-nav-${icon}`}
          className={({ isActive }) =>
            `bottom-nav__item${isActive ? ' bottom-nav__item--active' : ''}`
          }
        >
          <span className="material-symbols-outlined icon bottom-nav__icon">{icon}</span>
          <span className="bottom-nav__label">{t(labelKey)}</span>
        </NavLink>
      ))}
    </nav>
  );
}
