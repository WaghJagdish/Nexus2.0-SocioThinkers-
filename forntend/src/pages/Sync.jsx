import { useMemo, useState } from 'react';
import { useAppData } from '../context/AppDataContext';
import { useLanguage } from '../context/LanguageContext';
import './Sync.css';

export default function Sync() {
  const { t } = useLanguage();
  const { health, refreshHealth, documents, refreshDocuments, pendingQueue, status } = useAppData();
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');

  const progress = useMemo(() => {
    if (!health) return 25;
    if (pendingQueue.length) return 70;
    if (documents.length) return 90;
    return 100;
  }, [health, pendingQueue.length, documents.length]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncMessage('');
    try {
      await Promise.allSettled([refreshHealth(), refreshDocuments()]);
      setSyncMessage('Sync completed successfully!');
    } catch (error) {
      setSyncMessage(`Sync error: ${error.message}`);
    } finally {
      setSyncing(false);
    }
  };

  const circ = 2 * Math.PI * 120;
  const offset = circ * (1 - progress / 100);

  return (
    <div className="sync-page animate-fade-up">
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
            <p className="text-label-caps" style={{ color: 'rgba(0,77,64,0.6)', marginTop: 4 }}>
              {health ? 'Connected' : 'Disconnected'}
            </p>
          </div>
        </div>
        <button id="sync-now-btn" className="btn btn-primary sync-now-btn" onClick={handleSync} disabled={syncing}>
          <span className={`material-symbols-outlined icon icon-sm${syncing ? ' animate-spin-slow' : ''}`}>sync</span>
          {syncing ? 'Checking' : t('sync.syncNow')}
        </button>
      </section>

      {status.error && <div className="sync-error">{status.error}</div>}
      {syncMessage && (
        <div className={`sync-message ${syncMessage.includes('error') ? 'sync-message--error' : 'sync-message--success'}`}>
          <span className="material-symbols-outlined icon icon-sm">
            {syncMessage.includes('error') ? 'error' : 'check_circle'}
          </span>
          <p>{syncMessage}</p>
        </div>
      )}

      <div className="sync-bento">
        <div className="card-glass">
          <h3 className="text-h3 sync-bento__title">
            <span className="material-symbols-outlined icon" style={{ color: 'var(--color-primary-dark)' }}>check_circle</span>
            Backend status
          </h3>
          <div className="sync-list">
            <div className={`sync-list__item ${health ? 'sync-list__item--synced' : 'sync-list__item--pending'}`}>
              <div className={health ? 'sync-item-icon sync-item-icon--green' : 'sync-item-icon sync-item-icon--light'}>
                <span className="material-symbols-outlined icon icon-sm" style={{ color: health ? 'white' : 'var(--color-primary-dark)' }}>dns</span>
              </div>
              <div className="sync-item-text">
                <p style={{ fontWeight: 700, color: 'var(--color-primary-dark)' }}>{health ? health.status : 'Not reachable'}</p>
                <p style={{ fontSize: 12, color: 'var(--color-secondary)' }}>
                  {health ? `Version ${health.version}, ${health.agents_loaded ?? 0} agent(s)` : 'Start the FastAPI backend on the configured URL'}
                </p>
              </div>
              <span className="material-symbols-outlined icon" style={{ color: 'var(--color-primary-dark)', fontSize: 20 }}>
                {health ? 'verified' : 'warning'}
              </span>
            </div>
          </div>
        </div>

        <div className="card-glass">
          <h3 className="text-h3 sync-bento__title">
            <span className="material-symbols-outlined icon">pending_actions</span>
            Local queue
          </h3>
          <div className="sync-list">
            {pendingQueue.length ? pendingQueue.map((item) => (
              <div key={item.id} className="sync-list__item sync-list__item--pending">
                <div className="sync-item-icon sync-item-icon--light">
                  <span className="material-symbols-outlined icon icon-sm" style={{ color: 'var(--color-primary-dark)' }}>schedule</span>
                </div>
                <div className="sync-item-text">
                  <p style={{ fontWeight: 700, color: 'var(--color-primary-dark)' }}>{item.type} request</p>
                  <p style={{ fontSize: 12, color: 'var(--color-secondary)' }}>{item.reason}</p>
                </div>
              </div>
            )) : (
              <div className="sync-auto-note">
                <p>No local failed requests waiting.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <section className="card-glass sync-network">
        <div className="sync-network__img sync-network__icon">
          <span className="material-symbols-outlined icon-fill">folder_open</span>
        </div>
        <div className="sync-network__text">
          <h4 className="text-h3" style={{ color: 'var(--color-primary-dark)' }}>Generated documents</h4>
          <p className="text-body-md" style={{ color: 'var(--color-secondary)', marginTop: 8 }}>
            {documents.length ? `${documents.length} backend PDF document(s) available.` : 'No generated PDFs returned by backend yet.'}
          </p>
        </div>
      </section>
    </div>
  );
}
