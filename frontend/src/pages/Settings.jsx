import { useState } from 'react';
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
  const [offlineMode, setOfflineMode] = useState(true);
  const [pushNotif, setPushNotif] = useState(false);

  return (
    <div className="settings-page animate-fade-up">
      <div className="settings-header">
        <h2 className="text-h2" style={{ color: 'var(--color-primary)' }}>{t('settings.title')}</h2>
        <p className="text-body-md" style={{ color: 'var(--color-secondary)' }}>{t('settings.subtitle')}</p>
      </div>

      <div className="settings-grid">
        {/* Account Section */}
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
              <button className="account-avatar-edit" id="edit-avatar-btn" aria-label="Edit avatar">
                <span className="material-symbols-outlined icon-sm" style={{ fontSize: 16 }}>edit</span>
              </button>
            </div>
            <div className="account-fields">
              <div className="account-field">
                <label className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>{t('settings.fullName')}</label>
                <input
                  id="input-fullname"
                  type="text"
                  className="settings-input"
                  defaultValue="Arjun Patil"
                />
              </div>
              <div className="account-field">
                <label className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>{t('settings.email')}</label>
                <input
                  id="input-email"
                  type="email"
                  className="settings-input"
                  defaultValue="arjun.patil@kisansetu.in"
                />
              </div>
            </div>
          </div>
        </section>

        {/* App Preferences */}
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
              <Toggle id="toggle-offline" checked={offlineMode} onChange={e => setOfflineMode(e.target.checked)} />
            </div>
            <div className="pref-item">
              <div className="pref-item__left">
                <span className="material-symbols-outlined icon" style={{ color: 'var(--color-primary)' }}>notifications</span>
                <div>
                  <p className="text-body-md" style={{ fontWeight: 600 }}>{t('settings.pushNotifications')}</p>
                  <p style={{ fontSize: 12, color: 'var(--color-secondary)' }}>{t('settings.pushNotifDesc')}</p>
                </div>
              </div>
              <Toggle id="toggle-notif" checked={pushNotif} onChange={e => setPushNotif(e.target.checked)} />
            </div>
          </div>
        </section>

        {/* Data */}
        <section className="card-glass settings-section" id="settings-data">
          <div className="settings-section__header">
            <div className="settings-icon-wrap">
              <span className="material-symbols-outlined icon">database</span>
            </div>
            <h3 className="text-h3" style={{ color: 'var(--color-primary)' }}>{t('settings.data')}</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <button id="clear-cache-btn" className="data-action-btn data-action-btn--plain">
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className="material-symbols-outlined icon" style={{ color: 'var(--color-secondary)' }}>delete_sweep</span>
                <span style={{ fontWeight: 600 }}>{t('settings.clearCache')}</span>
              </div>
              <span className="material-symbols-outlined icon icon-sm" style={{ color: 'var(--color-outline)' }}>chevron_right</span>
            </button>
            <button id="export-all-btn" className="data-action-btn data-action-btn--primary">
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className="material-symbols-outlined icon icon-fill">download</span>
                <span style={{ fontWeight: 600 }}>{t('settings.exportAll')}</span>
              </div>
            </button>
          </div>
        </section>

        {/* Support */}
        <section className="card-glass settings-section settings-section--full" id="settings-support">
          <div className="settings-section__header">
            <div className="settings-icon-wrap">
              <span className="material-symbols-outlined icon">contact_support</span>
            </div>
            <h3 className="text-h3" style={{ color: 'var(--color-primary)' }}>{t('settings.support')}</h3>
          </div>
          <div className="support-grid">
            <a href="#help" className="support-link" id="help-center-link">
              <div className="support-icon">
                <span className="material-symbols-outlined icon" style={{ color: 'var(--color-primary)' }}>help_center</span>
              </div>
              <div>
                <p style={{ fontWeight: 700, color: 'var(--color-primary)', fontSize: 16 }}>{t('settings.helpCenter')}</p>
                <p style={{ fontSize: 12, color: 'var(--color-secondary)' }}>{t('settings.helpCenterDesc')}</p>
              </div>
            </a>
            <a href="#privacy" className="support-link" id="privacy-policy-link">
              <div className="support-icon">
                <span className="material-symbols-outlined icon" style={{ color: 'var(--color-primary)' }}>policy</span>
              </div>
              <div>
                <p style={{ fontWeight: 700, color: 'var(--color-primary)', fontSize: 16 }}>{t('settings.privacyPolicy')}</p>
                <p style={{ fontSize: 12, color: 'var(--color-secondary)' }}>{t('settings.privacyPolicyDesc')}</p>
              </div>
            </a>
          </div>
        </section>
      </div>

      <div className="settings-footer">
        <p className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>{t('settings.version')}</p>
        <p style={{ fontSize: 10, color: 'var(--color-outline)', letterSpacing: '0.2em', textTransform: 'uppercase', marginTop: 4 }}>
          {t('settings.crafted')}
        </p>
      </div>
    </div>
  );
}
