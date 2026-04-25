import { useLanguage } from '../context/LanguageContext';
import './Offline.css';

const FIELD_IMG = 'https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=900&q=80';

const PENDING_ITEMS = [
  { icon: 'potted_plant',  titleKey: 'offline.soilLog',     descKey: 'offline.soilLogDesc'   },
  { icon: 'photo_camera',  titleKey: 'offline.cropPhotos',  descKey: 'offline.cropPhotosDesc'},
  { icon: 'description',   titleKey: 'offline.fertReport',  descKey: 'offline.fertReportDesc'},
];

export default function Offline() {
  const { t } = useLanguage();

  return (
    <div className="offline-page animate-fade-up">
      {/* Offline Banner */}
      <div className="offline-banner">
        <span className="material-symbols-outlined icon icon-sm animate-pulse" style={{ color: '#2e7d32' }}>cloud_off</span>
        <span className="text-label-caps" style={{ color: '#2e7d32' }}>{t('offline.banner')}</span>
      </div>

      <div className="offline-content">
        {/* Hero */}
        <section className="offline-hero">
          <div className="offline-hero__text">
            <h2 className="text-h2">
              {t('offline.fieldStatus')}{' '}
              <span style={{ color: 'var(--color-primary-container)' }}>{t('offline.zone')}</span>
            </h2>
            <p className="text-body-lg" style={{ color: 'var(--color-on-surface-variant)', marginTop: 8 }}>
              {t('offline.description')}
            </p>
          </div>
          <div className="offline-hero__img-wrap">
            <img src={FIELD_IMG} alt="Agricultural fields" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>
        </section>

        {/* Bento Grid */}
        <div className="offline-bento">
          {/* Pending Items */}
          <div className="offline-pending">
            <div className="offline-pending__header">
              <h3 className="text-h3">{t('offline.pendingUpdates')}</h3>
              <span className="badge badge-pending">{PENDING_ITEMS.length} {t('offline.queued')}</span>
            </div>
            <div className="offline-pending__list">
              {PENDING_ITEMS.map((item, i) => (
                <div key={i} className="offline-pending__item">
                  <div className="offline-item__icon-wrap">
                    <span className="material-symbols-outlined icon" style={{ color: 'white' }}>{item.icon}</span>
                  </div>
                  <div className="offline-item__text">
                    <p style={{ fontWeight: 700 }}>{t(item.titleKey)}</p>
                    <p style={{ fontSize: 13, color: 'var(--color-secondary)' }}>{t(item.descKey)}</p>
                  </div>
                  <div className="offline-item__status">
                    <span className="material-symbols-outlined icon icon-sm" style={{ color: 'var(--color-primary)' }}>schedule</span>
                    <span className="text-label-caps" style={{ fontSize: 10 }}>{t('offline.pending')}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sidebar */}
          <div className="offline-sidebar">
            {/* Cached Weather */}
            <div className="card offline-weather">
              <div className="offline-weather__overlay" />
              <span className="text-label-caps" style={{ color: 'var(--color-outline)', position: 'relative' }}>{t('offline.cachedData')}</span>
              <div className="offline-weather__body">
                <div>
                  <p style={{ fontSize: 32, fontWeight: 800 }}>24°C</p>
                  <p style={{ fontSize: 13, color: 'var(--color-secondary)' }}>Partly Cloudy</p>
                </div>
                <span className="material-symbols-outlined" style={{ fontSize: 44, color: 'var(--color-primary-container)' }}>partly_cloudy_day</span>
              </div>
              <div className="offline-weather__footer">
                <p style={{ fontSize: 12, color: 'var(--color-primary)' }}>{t('offline.lastUpdated')}</p>
              </div>
            </div>

            {/* Tips */}
            <div className="card-glass offline-tips">
              <p className="text-label-caps" style={{ color: 'var(--color-on-surface-variant)' }}>{t('offline.offlineTips')}</p>
              <ul className="offline-tips__list">
                <li>
                  <span className="material-symbols-outlined icon-sm" style={{ color: 'var(--color-primary)', fontSize: 16 }}>check_circle</span>
                  <span>{t('offline.tip1')}</span>
                </li>
                <li>
                  <span className="material-symbols-outlined icon-sm" style={{ color: 'var(--color-primary)', fontSize: 16 }}>check_circle</span>
                  <span>{t('offline.tip2')}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Sync Notification */}
        <section className="offline-sync-card">
          <div className="offline-sync-card__icon">
            <span className="material-symbols-outlined icon icon-fill" style={{ color: 'white' }}>sync</span>
          </div>
          <div style={{ flex: 1 }}>
            <p style={{ fontWeight: 700, fontSize: 18 }}>{t('offline.itemsWaiting')}</p>
            <p style={{ fontSize: 13, opacity: 0.7 }}>{t('offline.syncResume')}</p>
          </div>
          <button id="retry-sync-btn" className="offline-retry-btn">{t('offline.retry')}</button>
        </section>
      </div>
    </div>
  );
}
