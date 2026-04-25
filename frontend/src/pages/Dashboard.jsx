import { useLanguage } from '../context/LanguageContext';
import './Dashboard.css';

// Placeholder farm field image (data URL compatible)
const GIS_IMG = 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1200&q=80';
const HEATMAP_IMG = 'https://images.unsplash.com/photo-1516251193007-45ef944ab0c6?w=1200&q=80';

export default function Dashboard() {
  const { t } = useLanguage();

  return (
    <div className="dashboard animate-fade-up">
      {/* Hero Grid */}
      <div className="dashboard__hero">
        {/* GIS Map Card */}
        <div className="gis-card">
          <img src={GIS_IMG} alt="GIS Suitability Map" className="gis-card__img" />
          <div className="gis-card__overlay">
            <div className="gis-card__location">
              <span className="material-symbols-outlined icon icon-sm" style={{ color: 'white' }}>location_on</span>
              <span className="text-label-caps" style={{ color: 'white' }}>{t('dashboard.location')}</span>
            </div>
            <h2 className="text-h2" style={{ color: 'white' }}>{t('dashboard.title')}</h2>
          </div>
          {/* Overlay badges */}
          <div className="gis-card__badges">
            <div className="gis-badge">
              <span className="gis-badge__dot gis-badge__dot--primary" />
              {t('dashboard.nitrogenHigh')}
            </div>
            <div className="gis-badge">
              <span className="gis-badge__dot gis-badge__dot--light" />
              {t('dashboard.optimalYield')}
            </div>
          </div>
        </div>

        {/* Recommendation Card */}
        <div className="recommendation-card">
          <div>
            <div className="recommendation-card__header">
              <span className="text-label-caps" style={{ opacity: 0.8 }}>{t('dashboard.finalAnalysis')}</span>
              <span className="material-symbols-outlined icon icon-fill" style={{ color: '#90d689' }}>verified</span>
            </div>
            <h3 className="text-h3" style={{ marginBottom: 4 }}>{t('dashboard.recommendedCrop')}</h3>
            <p className="rec-crop-name">Soybean</p>
          </div>
          <div className="recommendation-card__footer">
            <div className="fit-score">
              <div className="fit-score__icon">
                <span className="material-symbols-outlined icon">trending_up</span>
              </div>
              <div>
                <p className="fit-score__label">{t('dashboard.fitScore')}</p>
                <p className="fit-score__desc">{t('dashboard.fitScoreDesc')}</p>
              </div>
            </div>
            <button id="generate-plan-btn" className="btn btn-cta" style={{ width: '100%' }}>
              {t('dashboard.generatePlan')}
            </button>
          </div>
        </div>
      </div>

      {/* Data Grid */}
      <div className="dashboard__grid">
        {/* Soil Card */}
        <div className="card">
          <div className="card-header">
            <div className="card-icon-wrap">
              <span className="material-symbols-outlined icon">potted_plant</span>
            </div>
            <h4 className="text-h3">{t('dashboard.soilDiagnostics')}</h4>
          </div>
          <div className="soil-metrics">
            {[
              { label: t('dashboard.soilTexture'), value: 'Silty Clay', pct: 75 },
              { label: t('dashboard.phLevel'),     value: '7.2 Neutral', pct: 60 },
              { label: t('dashboard.moisture'),    value: '42%',         pct: 42 },
            ].map(({ label, value, pct }) => (
              <div key={label} className="soil-metric">
                <div className="soil-metric__top">
                  <span className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>{label}</span>
                  <span style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{value}</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* NPK Card */}
        <div className="card">
          <div className="card-header">
            <div className="card-icon-wrap">
              <span className="material-symbols-outlined icon">science</span>
            </div>
            <h4 className="text-h3">{t('dashboard.nutrients')}</h4>
            <span className="badge badge-pending" style={{ marginLeft: 'auto' }}>{t('dashboard.ppm')}</span>
          </div>
          <div className="npk-chart">
            {[
              { label: 'N', value: 184, pct: 120 },
              { label: 'P', value: 42,  pct: 80  },
              { label: 'K', value: 210, pct: 140 },
            ].map(({ label, value, pct }) => (
              <div key={label} className="npk-bar-group">
                <div className="npk-bar" style={{ height: pct + 'px' }} />
                <span className="npk-bar__value">{value}</span>
                <span className="text-label-caps" style={{ color: 'var(--color-secondary)' }}>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Climate Card */}
        <div className="card climate-card">
          <div className="card-header">
            <div className="card-icon-wrap">
              <span className="material-symbols-outlined icon">wb_sunny</span>
            </div>
            <h4 className="text-h3">{t('dashboard.climateOutlook')}</h4>
          </div>
          <div className="climate-temp">
            <div>
              <p className="text-h1" style={{ color: 'var(--color-primary)', fontWeight: 800 }}>24°C</p>
              <p style={{ color: 'var(--color-secondary)', fontWeight: 600, fontSize: 14 }}>{t('dashboard.humidity')}</p>
            </div>
            <span className="material-symbols-outlined" style={{ fontSize: 56, color: 'rgba(27,94,32,0.15)' }}>cloud</span>
          </div>
          <div className="climate-alert">
            <span className="material-symbols-outlined icon icon-sm" style={{ color: 'var(--color-primary)' }}>water_drop</span>
            <span style={{ fontWeight: 700, fontSize: 13 }}>{t('dashboard.rainAlert')}</span>
            <span className="material-symbols-outlined icon icon-sm" style={{ marginLeft: 'auto', color: 'var(--color-secondary)' }}>chevron_right</span>
          </div>
        </div>
      </div>

      {/* Yield Prediction Map */}
      <section className="yield-section">
        <div className="yield-section__header">
          <div>
            <h2 className="text-h2">{t('dashboard.yieldPrediction')}</h2>
            <p className="text-body-md" style={{ color: 'var(--color-secondary)' }}>{t('dashboard.yieldDesc')}</p>
          </div>
          <button id="export-data-btn" className="btn btn-secondary">
            <span className="material-symbols-outlined icon icon-sm">download</span>
            {t('dashboard.exportData')}
          </button>
        </div>
        <div className="yield-map">
          <img src={HEATMAP_IMG} alt="Yield Prediction Heatmap" className="yield-map__img" />
          <div className="yield-map__tint" />
          <div className="yield-legend glass">
            <p className="text-label-caps" style={{ color: 'var(--color-secondary)', marginBottom: 8 }}>{t('dashboard.legend')}</p>
            {[
              { color: 'var(--color-primary-container)', label: t('dashboard.highPotential') },
              { color: 'var(--color-primary-fixed-dim)', label: t('dashboard.standardYield') },
              { color: '#C8E6C9',                        label: t('dashboard.observationZone') },
            ].map(({ color, label }) => (
              <div key={label} className="yield-legend__item">
                <span className="yield-legend__dot" style={{ background: color }} />
                <span style={{ fontWeight: 700, fontSize: 12 }}>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
