import { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import './Sync.css';

const SAT_IMG = 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400&q=80';

const SYNCED = [
  { icon: 'potted_plant', titleKey: 'sync.fields',   descKey: 'sync.lastUpdated2m' },
  { icon: 'science',       titleKey: 'sync.soilData', descKey: 'sync.lastUpdated14m'},
  { icon: 'cloud',         titleKey: 'sync.weather',  descKey: 'sync.lastUpdated1h' },
];
const PENDING = [
  { icon: 'image',      titleKey: 'sync.cropImagery', descKey: 'sync.cropImagerySize'},
  { icon: 'monitoring', titleKey: 'sync.sensorLogs',  descKey: 'sync.sensorLogsSize' },
];

export default function Sync() {
  const { t } = useLanguage();
  const [progress, setProgress] = useState(82);
  const [syncing, setSyncing] = useState(false);

  const handleSync = () => {
    setSyncing(true);
    let p = progress;
    const iv = setInterval(() => {
      p = Math.min(100, p + Math.floor(Math.random() * 6) + 1);
      setProgress(p);
      if (p >= 100) { clearInterval(iv); setSyncing(false); }
    }, 200);
  };

  const circ = 2 * Math.PI * 120;
  const offset = circ * (1 - progress / 100);

  return (
    <div className="sync-page animate-fade-up">
      {/* Circular Progress */}
      <section className="sync-progress">
        <div className="sync-circle-wrap">
          <svg className="sync-circle-svg" viewBox="0 0 256 256">
            <circle cx="128" cy="128" r="120" fill="transparent" stroke="#d9e6da" strokeWidth="8" />
            <circle
              cx="128" cy="128" r="120"
              fill="transparent"
              stroke="#1b5e20"
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={circ}
              strokeDashoffset={offset}
              style={{ transition: 'stroke-dashoffset 0.4s ease', transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
            />
          </svg>
          <div className="sync-circle-inner">
            <div className="sync-circle-icon">
              <span className={`material-symbols-outlined icon${syncing ? ' animate-spin-slow' : ''}`} style={{ fontSize: 36, color: 'var(--color-primary-dark)' }}>sync</span>
            </div>
            <p className="text-h2" style={{ color: 'var(--color-primary-dark)', lineHeight: 1 }}>{progress}%</p>
            <p className="text-label-caps" style={{ color: 'rgba(0,77,64,0.6)', marginTop: 4 }}>{t('sync.syncing')}</p>
          </div>
        </div>
        <button id="sync-now-btn" className="btn btn-primary sync-now-btn" onClick={handleSync} disabled={syncing}>
          <span className={`material-symbols-outlined icon icon-sm${syncing ? ' animate-spin-slow' : ''}`}>sync</span>
          {t('sync.syncNow')}
        </button>
      </section>

      {/* Bento Grid */}
      <div className="sync-bento">
        {/* Recently Synced */}
        <div className="card-glass">
          <h3 className="text-h3 sync-bento__title">
            <span className="material-symbols-outlined icon" style={{ color: 'var(--color-primary-dark)' }}>check_circle</span>
            {t('sync.recentlySynced')}
          </h3>
          <div className="sync-list">
            {SYNCED.map(item => (
              <div key={item.titleKey} className="sync-list__item sync-list__item--synced">
                <div className="sync-item-icon sync-item-icon--green">
                  <span className="material-symbols-outlined icon icon-sm" style={{ color: 'white' }}>{item.icon}</span>
                </div>
                <div className="sync-item-text">
                  <p style={{ fontWeight: 700, color: 'var(--color-primary-dark)' }}>{t(item.titleKey)}</p>
                  <p style={{ fontSize: 12, color: 'var(--color-secondary)' }}>{t(item.descKey)}</p>
                </div>
                <span className="material-symbols-outlined icon" style={{ color: 'var(--color-primary-dark)', fontSize: 20 }}>verified</span>
              </div>
            ))}
          </div>
        </div>

        {/* Pending Uploads */}
        <div className="card-glass">
          <h3 className="text-h3 sync-bento__title">
            <span className="material-symbols-outlined icon">pending_actions</span>
            {t('sync.pendingUploads')}
          </h3>
          <div className="sync-list">
            {PENDING.map(item => (
              <div key={item.titleKey} className="sync-list__item sync-list__item--pending">
                <div className="sync-item-icon sync-item-icon--light">
                  <span className="material-symbols-outlined icon icon-sm" style={{ color: 'var(--color-primary-dark)' }}>{item.icon}</span>
                </div>
                <div className="sync-item-text">
                  <p style={{ fontWeight: 700, color: 'var(--color-primary-dark)' }}>{t(item.titleKey)}</p>
                  <p style={{ fontSize: 12, color: 'var(--color-secondary)' }}>{t(item.descKey)}</p>
                </div>
                <span className="material-symbols-outlined icon" style={{ color: 'rgba(27,94,32,0.5)', fontSize: 20 }}>schedule</span>
              </div>
            ))}
            <div className="sync-auto-note">
              <p>{t('sync.autoSync')}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Network Optimization */}
      <section className="card-glass sync-network">
        <div className="sync-network__img">
          <img src={SAT_IMG} alt="Satellite connection" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>
        <div className="sync-network__text">
          <h4 className="text-h3" style={{ color: 'var(--color-primary-dark)' }}>{t('sync.networkOptimization')}</h4>
          <p className="text-body-md" style={{ color: 'var(--color-secondary)', marginTop: 8 }}>{t('sync.networkDesc')}</p>
        </div>
      </section>
    </div>
  );
}
