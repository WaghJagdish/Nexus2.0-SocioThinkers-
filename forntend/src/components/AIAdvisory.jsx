import { useLanguage } from '../context/LanguageContext';
import './AIAdvisory.css';

export default function AIAdvisory({ responseText, isLoading, onViewDocs }) {
  const { t } = useLanguage();
  return (
    <div className="ai-advisory">
      <div className="ai-advisory__header">
        <div className="ai-advisory__title-wrap">
          <span className="material-symbols-outlined icon-fill">psychology</span>
          <h3 className="text-h3">{t('dashboard.aiAdvisory')}</h3>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={onViewDocs}>
          <span className="material-symbols-outlined icon icon-sm">description</span>
          {t('dashboard.docs')}
        </button>
      </div>

      <div className="ai-advisory__content">
        {isLoading ? (
          <div className="ai-advisory__skeleton">
            <div className="skeleton-line" style={{ width: '100%' }} />
            <div className="skeleton-line" style={{ width: '95%' }} />
            <div className="skeleton-line" style={{ width: '90%' }} />
            <div className="skeleton-line" style={{ width: '85%' }} />
          </div>
        ) : responseText ? (
          <>
            <div className="ai-advisory__bg-icon">
              <span className="material-symbols-outlined icon-fill">spa</span>
            </div>
            <div className="ai-advisory__text">
              {responseText.split('\n').map((para, i) => 
                para.trim() && (
                  <p key={i} className="advisory-paragraph">
                    {para}
                  </p>
                )
              )}
            </div>
          </>
        ) : (
          <div className="ai-advisory__empty">
            <span className="material-symbols-outlined icon-fill">temp_preferences_eco</span>
            <h4 className="text-h4">{t('advisory.noAdvisory')}</h4>
            <p className="text-body-md">{t('advisory.noAdvisoryDesc')}</p>
          </div>
        )}
      </div>
    </div>
  );
}
