import { useNavigate } from 'react-router-dom';
import { useAppData } from '../context/AppDataContext';
import { useLanguage } from '../context/LanguageContext';
import './Fields.css';

export default function Fields() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { latestResult, status } = useAppData();
  const schemes = latestResult?.matched_schemes || [];

  return (
    <div className="fields animate-fade-up">
      <div className="fields__header">
        <div>
          <h1 className="text-h2" style={{ color: 'var(--color-primary-dark)' }}>{t('fields.title')}</h1>
          <p className="text-body-md fields__subheader">{t('fields.subtitle')}</p>
        </div>
      </div>

      {status.error && (
        <div className="fields__error-banner">
          <span className="material-symbols-outlined icon icon-sm">error</span>
          <div>
            <p style={{ fontWeight: 700, margin: 0 }}>{t('fields.error')}</p>
            <p style={{ margin: 0, fontSize: '12px', opacity: 0.8 }}>{status.error}</p>
          </div>
        </div>
      )}

      <div className="fields__grid" style={{ gridTemplateColumns: '1fr' }}>
        <div className="field-card">
          <div className="field-card__top" style={{ background: 'linear-gradient(135deg, #1b5e20, #004d40)' }}>
            <span className="material-symbols-outlined icon-fill" style={{ fontSize: 40, color: 'rgba(255,255,255,0.2)', position: 'absolute', right: 16, top: 16 }}>account_balance</span>
            <div className="field-card__badge-wrap">
              <span className={`badge ${schemes.length > 0 ? 'badge-success' : 'badge-pending'}`}>{schemes.length || 0} {t('fields.schemes')}</span>
            </div>
            <div>
              <h3 className="text-h3" style={{ color: 'white', marginBottom: '4px' }}>{t('fields.eligibleSchemes')}</h3>
              <p style={{ color: 'rgba(255,255,255,0.7)', fontWeight: 600, fontSize: 14, margin: 0 }}>{t('fields.basedOnProfile')}</p>
            </div>
          </div>
          <div className="field-card__body">
            {schemes.length ? (
              <div className="scheme-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {schemes.map((scheme) => (
                  <div className="scheme-item" key={scheme.id || scheme.name} style={{ background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="material-symbols-outlined icon icon-sm" style={{ color: 'var(--color-primary)' }}>verified</span>
                      <strong style={{ fontSize: '18px', color: 'var(--color-primary-dark)' }}>{scheme.name || 'Government Scheme'}</strong>
                    </div>
                    <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-on-surface)', lineHeight: '1.5' }}>
                      {scheme.benefits || scheme.benefit || scheme.category || 'Benefit details returned by backend'}
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginTop: '4px' }}>
                      <button
                        className="btn btn-primary"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '14px', fontWeight: 700, padding: '8px 16px', minHeight: 'auto', borderRadius: '10px' }}
                        onClick={() => navigate('/scheme-chat', { state: { schemeName: scheme.name, schemeData: scheme, mode: 'apply' } })}
                      >
                        <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>description</span>
                        {t('fields.applyNow')}
                      </button>
                      <button
                        className="btn btn-ghost"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '14px', color: 'var(--color-primary-dark)', fontWeight: 600, padding: '8px 12px', minHeight: 'auto' }}
                        onClick={() => navigate('/scheme-chat', { state: { schemeName: scheme.name, schemeData: scheme, mode: 'info' } })}
                      >
                        <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>chat</span>
                        {t('fields.askAi')}
                      </button>
                      {scheme.link && (
                        <a href={scheme.link} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '13px', color: '#059669', textDecoration: 'none', fontWeight: 600 }}>
                          <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>open_in_new</span>
                          {t('fields.applyReadMore')}
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="field-card__empty">
                <span className="material-symbols-outlined icon" style={{ fontSize: '40px', color: 'var(--color-surface-container)' }}>account_tree</span>
                <p className="text-body-md">{t('fields.noSchemes')}</p>
                <p style={{ fontSize: '12px', color: 'var(--color-secondary)' }}>{t('fields.noSchemesHint')}</p>
                <button
                  className="btn btn-secondary"
                  style={{ marginTop: '10px', width: '100%' }}
                  onClick={() => navigate('/voice')}
                >
                  <span className="material-symbols-outlined icon icon-sm">mic</span>
                  {t('fields.querySchemes')}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
