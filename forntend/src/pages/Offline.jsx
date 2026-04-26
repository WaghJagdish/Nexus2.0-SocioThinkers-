import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppData } from '../context/AppDataContext';
import { useLanguage } from '../context/LanguageContext';
import './Offline.css';

export default function Offline() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { pendingQueue, health, refreshHealth, clearLocalData, latestResult, status } = useAppData();
  const [retryMessage, setRetryMessage] = useState('');
  const [isClearing, setIsClearing] = useState(false);

  const handleRetry = async () => {
    setRetryMessage('');
    try {
      await refreshHealth();
      setRetryMessage('Connection check complete!');
    } catch (error) {
      setRetryMessage(`Connection failed: ${error.message}`);
    }
  };

  const handleClear = async () => {
    setIsClearing(true);
    try {
      clearLocalData();
      setRetryMessage('Local queue cleared successfully.');
    } catch (error) {
      setRetryMessage(`Clear error: ${error.message}`);
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <div className="offline-page animate-fade-up">
      <div className="offline-banner">
        <span className="material-symbols-outlined icon icon-sm animate-pulse" style={{ color: health ? '#2e7d32' : '#ba1a1a' }}>
          {health ? 'cloud_done' : 'cloud_off'}
        </span>
        <span className="text-label-caps" style={{ color: health ? '#2e7d32' : '#ba1a1a' }}>
          {health ? 'Backend online' : t('offline.banner')}
        </span>
      </div>

      <div className="offline-content">
        <section className="offline-hero offline-real-hero">
          <div className="offline-hero__text">
            <h2 className="text-h2">
              Local request queue{' '}
              <span style={{ color: 'var(--color-primary-container)' }}>{pendingQueue.length}</span>
            </h2>
            <p className="text-body-lg" style={{ color: 'var(--color-on-surface-variant)', marginTop: 8 }}>
              Failed voice uploads are recorded here so the app does not pretend they were processed.
            </p>
          </div>
        </section>

        <div className="offline-bento">
          <div className="offline-pending">
            <div className="offline-pending__header">
              <h3 className="text-h3">{t('offline.pendingUpdates')}</h3>
              <span className="badge badge-pending">{pendingQueue.length} {t('offline.queued')}</span>
            </div>
            <div className="offline-pending__list">
              {pendingQueue.length ? pendingQueue.map((item) => (
                <div key={item.id} className="offline-pending__item">
                  <div className="offline-item__icon-wrap">
                    <span className="material-symbols-outlined icon" style={{ color: 'white' }}>mic</span>
                  </div>
                  <div className="offline-item__text">
                    <p style={{ fontWeight: 700 }}>{item.type} request</p>
                    <p style={{ fontSize: 13, color: 'var(--color-secondary)' }}>{item.reason}</p>
                  </div>
                  <div className="offline-item__status">
                    <span className="material-symbols-outlined icon icon-sm" style={{ color: 'var(--color-primary)' }}>schedule</span>
                    <span className="text-label-caps" style={{ fontSize: 10 }}>{t('offline.pending')}</span>
                  </div>
                </div>
              )) : (
                <div className="offline-pending__item">
                  <div className="offline-item__icon-wrap">
                    <span className="material-symbols-outlined icon" style={{ color: 'white' }}>done</span>
                  </div>
                  <div className="offline-item__text">
                    <p style={{ fontWeight: 700 }}>No local queue</p>
                    <p style={{ fontSize: 13, color: 'var(--color-secondary)' }}>All visible data is either returned by backend or user-entered.</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="offline-sidebar">
            <div className="card offline-weather">
              <span className="text-label-caps" style={{ color: 'var(--color-outline)', position: 'relative' }}>Latest advisory</span>
              <div className="offline-weather__body">
                <div>
                  <p style={{ fontSize: 22, fontWeight: 800 }}>{latestResult?.recommended_crop || 'None'}</p>
                  <p style={{ fontSize: 13, color: 'var(--color-secondary)' }}>{latestResult?.status || 'No backend response cached'}</p>
                </div>
                <span className="material-symbols-outlined" style={{ fontSize: 44, color: 'var(--color-primary-container)' }}>history</span>
              </div>
            </div>

            <div className="card-glass offline-tips">
              <p className="text-label-caps" style={{ color: 'var(--color-on-surface-variant)' }}>{t('offline.offlineTips')}</p>
              <ul className="offline-tips__list">
                <li>
                  <span className="material-symbols-outlined icon-sm" style={{ color: 'var(--color-primary)', fontSize: 16 }}>check_circle</span>
                  <span>Start the backend before using live analysis.</span>
                </li>
                <li>
                  <span className="material-symbols-outlined icon-sm" style={{ color: 'var(--color-primary)', fontSize: 16 }}>check_circle</span>
                  <span>Use Settings to confirm the API URL.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <section className="offline-sync-card">
          <div className="offline-sync-card__icon">
            <span className="material-symbols-outlined icon icon-fill" style={{ color: 'white' }}>sync</span>
          </div>
          <div style={{ flex: 1 }}>
            <p style={{ fontWeight: 700, fontSize: 18 }}>{pendingQueue.length} item(s) waiting</p>
            <p style={{ fontSize: 13, opacity: 0.7 }}>Retry checks connectivity. Clear removes local failed-request records.</p>
          </div>
          <button
            id="retry-sync-btn"
            className="offline-retry-btn"
            onClick={handleRetry}
            disabled={status.loading}
          >
            {status.loading ? 'Checking...' : 'Retry'}
          </button>
          <button
            className="offline-retry-btn"
            onClick={handleClear}
            disabled={isClearing || pendingQueue.length === 0}
          >
            {isClearing ? 'Clearing...' : 'Clear'}
          </button>
          <button className="offline-retry-btn" onClick={() => navigate('/voice')}>Ask</button>
        </section>

        {retryMessage && (
          <div className={`offline-message ${retryMessage.includes('failed') ? 'offline-message--error' : 'offline-message--success'}`}>
            <span className="material-symbols-outlined icon icon-sm">
              {retryMessage.includes('failed') ? 'error' : 'check_circle'}
            </span>
            <p>{retryMessage}</p>
          </div>
        )}
      </div>
    </div>
  );
}
