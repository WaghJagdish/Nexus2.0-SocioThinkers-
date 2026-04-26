import { useState } from 'react';
import { useAppData } from '../context/AppDataContext';
import { useLanguage } from '../context/LanguageContext';
import './Settings.css';

function Toggle({ checked, onChange, id }) {
  return (
    <label className="toggle-wrap" htmlFor={id}>
      <input
        id={id}
        type="checkbox"
        className="toggle-input sr-only"
        checked={checked}
        onChange={onChange}
      />
      <div className="toggle-track">
        <div className="toggle-thumb" style={{ transform: checked ? 'translateX(20px)' : 'translateX(0)' }} />
      </div>
    </label>
  );
}

export default function Settings() {
  const { t } = useLanguage();
  const {
    apiBase,
    updateApiBase,
    profile,
    updateProfile,
    useCurrentLocation,
    refreshHealth,
    health,
    latestResult,
    pendingQueue,
    clearLocalData,
  } = useAppData();
  const [apiValue, setApiValue] = useState(apiBase);
  const [offlineMode, setOfflineMode] = useState(true);
  const [pushNotif, setPushNotif] = useState(false);
  const [message, setMessage] = useState('');

  const saveApi = async () => {
    if (!apiValue.trim()) {
      setMessage('API URL cannot be empty.');
      return;
    }
    try {
      updateApiBase(apiValue);
      setMessage('API URL saved. Checking connection...');
      await refreshHealth();
      setMessage('Connected successfully!');
    } catch (error) {
      setMessage(`Connection failed: ${error.message}`);
    }
  };

  const captureLocation = async () => {
    try {
      const coords = await useCurrentLocation();
      setMessage(`Location saved: ${coords.latitude}, ${coords.longitude}`);
    } catch (error) {
      setMessage(error.message);
    }
  };

  const exportLocalData = () => {
    const payload = {
      profile,
      latestResult,
      pendingQueue,
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `kisansetu-export-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="settings-page animate-fade-up">
      <div className="settings-header">
        <h2 className="text-h2" style={{ color: 'var(--color-primary)' }}>{t('settings.title')}</h2>
        <p className="text-body-md" style={{ color: 'var(--color-secondary)' }}>{t('settings.subtitle')}</p>
      </div>

      {message && (
        <div className={`settings-message ${message.includes('failed') || message.includes('Error') ? 'settings-message--error' : 'settings-message--success'}`}>
          <span className="material-symbols-outlined icon icon-sm">
            {message.includes('failed') || message.includes('Error') ? 'error' : 'check_circle'}
          </span>
          <p>{message}</p>
        </div>
      )}

      <div className="settings-grid">
        <section className="card-glass settings-section settings-section--full" id="settings-account">
          <div className="settings-section__header">
            <div className="settings-icon-wrap">
              <span className="material-symbols-outlined icon">person</span>
            </div>
            <h3 className="text-h3" style={{ color: 'var(--color-primary)' }}>{t('settings.account')}</h3>
          </div>
          <div className="account-card">
            <div className="account-avatar-wrap">
              <div className="account-avatar">
                <span className="material-symbols-outlined icon-fill" style={{ fontSize: 56, color: 'var(--color-primary-dark)' }}>account_circle</span>
              </div>
            </div>
            <div className="account-fields">
              <div className="account-field">
                <label className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>{t('settings.userId')}</label>
                <input
                  id="input-userid"
                  type="text"
                  className="settings-input"
                  value={profile.userId}
                  onChange={(event) => updateProfile({ userId: event.target.value })}
                />
              </div>
              <div className="account-field">
                <label className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>{t('settings.fullName')}</label>
                <input
                  id="input-fullname"
                  type="text"
                  className="settings-input"
                  value={profile.fullName}
                  onChange={(event) => updateProfile({ fullName: event.target.value })}
                  placeholder={t('settings.yourName')}
                />
              </div>
              <div className="account-field">
                <label className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>{t('settings.email')}</label>
                <input
                  id="input-email"
                  type="email"
                  className="settings-input"
                  value={profile.email}
                  onChange={(event) => updateProfile({ email: event.target.value })}
                  placeholder={t('settings.optional')}
                />
              </div>
            </div>
          </div>
        </section>

        <section className="card-glass settings-section settings-section--full" id="settings-backend">
          <div className="settings-section__header">
            <div className="settings-icon-wrap">
              <span className="material-symbols-outlined icon">dns</span>
            </div>
            <h3 className="text-h3" style={{ color: 'var(--color-primary)' }}>{t('settings.backend')}</h3>
          </div>
          <div className="account-fields">
            <div className="account-field">
              <label className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>{t('settings.apiUrl')}</label>
              <input
                id="input-api"
                type="url"
                className="settings-input"
                value={apiValue}
                onChange={(event) => setApiValue(event.target.value)}
              />
            </div>
            <button className="btn btn-primary" type="button" onClick={saveApi}>
              <span className="material-symbols-outlined icon icon-sm">save</span>
              {t('settings.saveAndCheck')}
            </button>
            <p className="text-body-md" style={{ color: 'var(--color-secondary)' }}>
              {health ? t('settings.connectedInfo').replace('{status}', health.status).replace('{version}', health.version).replace('{agents}', health.agents_loaded ?? 0) : t('settings.notConnected')}
            </p>
          </div>
        </section>

        <section className="card-glass settings-section" id="settings-preferences">
          <div className="settings-section__header">
            <div className="settings-icon-wrap">
              <span className="material-symbols-outlined icon">tune</span>
            </div>
            <h3 className="text-h3" style={{ color: 'var(--color-primary)' }}>{t('settings.appPreferences')}</h3>
          </div>
          <div className="pref-list">
            <div className="pref-item">
              <div className="pref-item__left">
                <span className="material-symbols-outlined icon" style={{ color: 'var(--color-primary)' }}>cloud_off</span>
                <div>
                  <p className="text-body-md" style={{ fontWeight: 600 }}>{t('settings.offlineMode')}</p>
                  <p style={{ fontSize: 12, color: 'var(--color-secondary)' }}>{t('settings.offlineModeDesc')}</p>
                </div>
              </div>
              <Toggle id="toggle-offline" checked={offlineMode} onChange={(event) => setOfflineMode(event.target.checked)} />
            </div>
            <div className="pref-item">
              <div className="pref-item__left">
                <span className="material-symbols-outlined icon" style={{ color: 'var(--color-primary)' }}>notifications</span>
                <div>
                  <p className="text-body-md" style={{ fontWeight: 600 }}>{t('settings.pushNotifications')}</p>
                  <p style={{ fontSize: 12, color: 'var(--color-secondary)' }}>{t('settings.pushNotifDesc')}</p>
                </div>
              </div>
              <Toggle
                id="toggle-notif"
                checked={pushNotif}
                onChange={async (event) => {
                  setPushNotif(event.target.checked);
                  if (event.target.checked && Notification?.requestPermission) await Notification.requestPermission();
                }}
              />
            </div>
          </div>
        </section>

        <section className="card-glass settings-section" id="settings-data">
          <div className="settings-section__header">
            <div className="settings-icon-wrap">
              <span className="material-symbols-outlined icon">database</span>
            </div>
            <h3 className="text-h3" style={{ color: 'var(--color-primary)' }}>{t('settings.data')}</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <button id="location-btn" className="data-action-btn data-action-btn--plain" onClick={captureLocation}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className="material-symbols-outlined icon" style={{ color: 'var(--color-secondary)' }}>my_location</span>
                <span style={{ fontWeight: 600 }}>{profile.latitude ? `${profile.latitude}, ${profile.longitude}` : t('settings.captureGps')}</span>
              </div>
              <span className="material-symbols-outlined icon icon-sm" style={{ color: 'var(--color-outline)' }}>chevron_right</span>
            </button>
            <button id="clear-cache-btn" className="data-action-btn data-action-btn--plain" onClick={clearLocalData}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className="material-symbols-outlined icon" style={{ color: 'var(--color-secondary)' }}>delete_sweep</span>
                <span style={{ fontWeight: 600 }}>{t('settings.clearCache')}</span>
              </div>
              <span className="material-symbols-outlined icon icon-sm" style={{ color: 'var(--color-outline)' }}>chevron_right</span>
            </button>
            <button id="export-all-btn" className="data-action-btn data-action-btn--primary" onClick={exportLocalData}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className="material-symbols-outlined icon icon-fill">download</span>
                <span style={{ fontWeight: 600 }}>{t('settings.exportAll')}</span>
              </div>
            </button>
          </div>
        </section>

        <section className="card-glass settings-section settings-section--full" id="settings-support">
          <div className="settings-section__header">
            <div className="settings-icon-wrap">
              <span className="material-symbols-outlined icon">contact_support</span>
            </div>
            <h3 className="text-h3" style={{ color: 'var(--color-primary)' }}>{t('settings.support')}</h3>
          </div>
          <div className="support-grid">
            <a href="https://fastapi.tiangolo.com/" target="_blank" rel="noreferrer" className="support-link" id="help-center-link">
              <div className="support-icon">
                <span className="material-symbols-outlined icon" style={{ color: 'var(--color-primary)' }}>help_center</span>
              </div>
              <div>
                <p style={{ fontWeight: 700, color: 'var(--color-primary)', fontSize: 16 }}>{t('settings.backendDocs')}</p>
                <p style={{ fontSize: 12, color: 'var(--color-secondary)' }}>{t('settings.backendDocsDesc')}</p>
              </div>
            </a>
            <a href="https://www.bhashini.ai/docs" target="_blank" rel="noreferrer" className="support-link" id="privacy-policy-link">
              <div className="support-icon">
                <span className="material-symbols-outlined icon" style={{ color: 'var(--color-primary)' }}>record_voice_over</span>
              </div>
              <div>
                <p style={{ fontWeight: 700, color: 'var(--color-primary)', fontSize: 16 }}>{t('settings.speechDocs')}</p>
                <p style={{ fontSize: 12, color: 'var(--color-secondary)' }}>{t('settings.speechDocsDesc')}</p>
              </div>
            </a>
          </div>
        </section>
      </div>

      <div className="settings-footer">
        <p className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>{t('settings.version')}</p>
        <p style={{ fontSize: 10, color: 'var(--color-outline)', letterSpacing: '0.2em', textTransform: 'uppercase', marginTop: 4 }}>
          {t('settings.realBackend')}
        </p>
      </div>
    </div>
  );
}
