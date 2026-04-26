import { useEffect, useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import './GISSuitabilityMap.css';

export default function GISSuitabilityMap({ latitude, longitude, gisData, isLoading }) {
  const { t } = useLanguage();
  const [mapStatus, setMapStatus] = useState('idle');

  useEffect(() => {
    if (gisData && latitude && longitude) {
      setMapStatus('loaded');
    }
  }, [gisData, latitude, longitude]);

  const getTextureColor = (texture) => {
    if (!texture) return '#9C9C9C';
    const t = texture.toLowerCase();
    if (t === 'laterite') return '#B84C2A';
    if (t === 'silty_clay' || t === 'silty clay') return '#7A6352';
    if (t === 'clay_loam' || t === 'clay loam') return '#8B6F47';
    if (t === 'sandy_loam' || t === 'sandy loam') return '#C9A96E';
    if (t === 'silty_loam' || t === 'silty loam') return '#96836B';
    if (t.includes('sandy')) return '#C2A05A';
    if (t.includes('clay')) return '#6B4F3A';
    if (t.includes('alluvial')) return '#A09070';
    if (t.includes('loam')) return '#6B5D4F';
    return '#9C9C9C';
  };

  const getDepthLabel = (depth) => {
    if (depth == null) return t('gis.unknown');
    const cm = typeof depth === 'number' ? depth : parseFloat(depth);
    if (!isNaN(cm)) {
      if (cm < 50) return `${t('gis.shallow')} (${cm} cm)`;
      if (cm < 90) return `${t('gis.medium')} (${cm} cm)`;
      if (cm < 150) return `${t('gis.deep')} (${cm} cm)`;
      return `${t('gis.veryDeep')} (${cm} cm)`;
    }
    const d = String(depth).toLowerCase();
    if (d.includes('shallow')) return t('gis.shallow');
    if (d.includes('medium')) return t('gis.medium');
    if (d.includes('deep')) return t('gis.deep');
    if (d.includes('very')) return t('gis.veryDeep');
    return String(depth);
  };

  const getTextureLabel = (texture) => {
    if (!texture) return t('gis.unknown');
    const keyMap = {
      'clayey': 'clay', 'loamy': 'loam', 'sandy': 'sandy', 'alluvial': 'alluvial',
      'sandy_loam': 'sandyLoam', 'clay_loam': 'clayLoam',
      'silty_clay': 'siltyClay', 'silty_loam': 'siltyLoam', 'laterite': 'laterite',
    };
    const k = keyMap[texture.toLowerCase()];
    return k ? t(`gis.${k}`) : texture;
  };

  const getDrainageLabel = (drainage) => {
    if (!drainage) return t('gis.unknown');
    const keyMap = { 'poor': 'dashboard.poor', 'moderate': 'dashboard.fair', 'good': 'dashboard.good', 'well': 'gis.wellDrained' };
    const k = keyMap[drainage.toLowerCase()];
    return k ? t(k) : drainage;
  };

  return (
    <div className="gis-suitability-map">
      <div className="gis-map__header">
        <div className="gis-map__title-wrap">
          <span className="material-symbols-outlined icon-fill">public</span>
          <h3 className="text-h3">{t('dashboard.gisSoilAnalysis')}</h3>
        </div>
        {latitude && longitude && (
          <span className="text-body-sm gis-map__coordinates">
            {latitude.toFixed(4)}° N, {longitude.toFixed(4)}° E
          </span>
        )}
      </div>

      <div className="gis-map__container">
        {isLoading ? (
          <div className="gis-map__skeleton">
            <div className="skeleton-circle" />
            <div className="skeleton-text" style={{ width: '80%', height: '12px', marginTop: '20px' }} />
            <div className="skeleton-text" style={{ width: '60%', height: '12px', marginTop: '8px' }} />
          </div>
        ) : gisData ? (
          <>
            <div className="gis-map__visual">
              <div
                className="gis-map__soil-circle"
                style={{
                  background: `linear-gradient(135deg, ${getTextureColor(gisData.soil_texture)} 0%, ${getTextureColor(gisData.soil_texture)}AA 100%)`
                }}
              >
                <div className="gis-map__soil-depth-indicator" style={{ opacity: Math.min(1, (parseFloat(gisData.soil_depth_cm) || parseFloat(gisData.soil_depth) || 50) / 150) }}>
                  <span className="text-label-caps">{t('dashboard.depth')}</span>
                </div>
              </div>
            </div>

            <div className="gis-map__metrics">
              <div className="gis-metric">
                <div className="gis-metric__label">
                  <span className="material-symbols-outlined icon">layers</span>
                  {t('dashboard.soilTexture')}
                </div>
                <div className="gis-metric__value">
                  {getTextureLabel(gisData.soil_texture)}
                </div>
              </div>

              <div className="gis-metric">
                <div className="gis-metric__label">
                  <span className="material-symbols-outlined icon">height</span>
                  {t('dashboard.soilDepth')}
                </div>
                <div className="gis-metric__value">
                  {getDepthLabel(gisData.soil_depth_cm ?? gisData.soil_depth)}
                </div>
              </div>

              <div className="gis-metric">
                <div className="gis-metric__label">
                  <span className="material-symbols-outlined icon">water_drop</span>
                  {t('dashboard.drainage')}
                </div>
                <div className="gis-metric__value">
                  {getDrainageLabel(gisData.soil_drainage)}
                </div>
              </div>

              <div className="gis-metric">
                <div className="gis-metric__label">
                  <span className="material-symbols-outlined icon">science</span>
                  {t('dashboard.phLevel')}
                </div>
                <div className="gis-metric__value">
                  {gisData.ph_range || '6.5'}
                </div>
              </div>

              {gisData.organic_carbon && (
                <div className="gis-metric">
                  <div className="gis-metric__label">
                    <span className="material-symbols-outlined icon">compost</span>
                    {t('gis.organicCarbon')}
                  </div>
                  <div className="gis-metric__value">
                    {gisData.organic_carbon}
                  </div>
                </div>
              )}
            </div>

            {gisData.source && (
              <div style={{ padding: '8px 16px', fontSize: '11px', color: 'var(--color-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>
                  {gisData.is_estimated ? 'auto_fix_high' : 'verified'}
                </span>
                {t('gis.source')}: {gisData.source === 'isric_soilgrids' ? t('gis.isricSource') : gisData.source === 'llm_estimation' ? t('gis.aiEstimation') : gisData.source}
                {gisData.is_estimated && ` (${t('gis.estimated')})`}
              </div>
            )}

            <div className="gis-map__suitability-bar">
              <div className="suitability-scale">
                <div className="suitability-scale__item">
                  <div className="suitability-scale__color poor" />
                  <span className="text-label-sm">{t('dashboard.poor')}</span>
                </div>
                <div className="suitability-scale__item">
                  <div className="suitability-scale__color fair" />
                  <span className="text-label-sm">{t('dashboard.fair')}</span>
                </div>
                <div className="suitability-scale__item">
                  <div className="suitability-scale__color good" />
                  <span className="text-label-sm">{t('dashboard.good')}</span>
                </div>
                <div className="suitability-scale__item">
                  <div className="suitability-scale__color excellent" />
                  <span className="text-label-sm">{t('dashboard.excellent')}</span>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="gis-map__empty">
            <span className="material-symbols-outlined icon-fill">
              {latitude && longitude ? 'analytics' : 'location_off'}
            </span>
            <p className="text-body-md">
              {latitude && longitude 
                ? t('gis.runAnalysis') 
                : t('gis.setLocation')}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
