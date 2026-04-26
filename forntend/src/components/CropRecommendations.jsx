import { useState, useEffect } from 'react';
import { getCropImage, getCropInfo, getCropSuitabilityColor, getCropSuitabilityLabel } from '../services/cropImagesLocal';
import { useLanguage } from '../context/LanguageContext';
import './CropRecommendations.css';

export default function CropRecommendations({
  recommendations = [],
  gisData = null,
  isLoading = false,
  latitude,
  longitude,
}) {
  const [selectedCrop, setSelectedCrop] = useState(null);
  const [cropImages, setCropImages] = useState({});
  const { t } = useLanguage();

  useEffect(() => {
    if (recommendations.length > 0 && !selectedCrop) {
      setSelectedCrop(recommendations[0]);
    }
  }, [recommendations, selectedCrop]);

  useEffect(() => {
    const loadImages = async () => {
      const images = {};
      for (const rec of recommendations.slice(0, 3)) {
        try {
          images[rec.crop_name] = await getCropImage(rec.crop_name);
        } catch (error) {
          console.warn(`Failed to load image for ${rec.crop_name}:`, error);
          images[rec.crop_name] = getCropInfo(rec.crop_name).fallback;
        }
      }
      setCropImages(images);
    };

    if (recommendations.length > 0) {
      loadImages();
    }
  }, [recommendations]);

  if (isLoading) {
    return (
      <div className="crop-recommendations crop-recommendations--skeleton">
        <div className="skeleton-card" />
        <div className="skeleton-card" />
        <div className="skeleton-card" />
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="crop-recommendations crop-recommendations--empty">
        <span className="material-symbols-outlined">agriculture</span>
        <h3>{t('crops.noRecommendations')}</h3>
        <p>{t('crops.noRecommendationsDesc')}</p>
      </div>
    );
  }

  return (
    <div className="crop-recommendations">
      <div className="crop-recommendations__header">
        <h2 className="text-h3">{t('dashboard.recommendedCrops')}</h2>
        <p className="text-body-sm">{t('dashboard.basedOnGis')}</p>
      </div>

      <div className="crop-recommendations__list">
        {recommendations.slice(0, 3).map((crop, idx) => (
          <div
            key={`${crop.crop_name}-${idx}`}
            className={`crop-card ${selectedCrop?.crop_name === crop.crop_name ? 'crop-card--active' : ''}`}
            onClick={() => setSelectedCrop(crop)}
          >
            <div className="crop-card__image-wrapper">
              <img
                src={cropImages[crop.crop_name] || getCropInfo(crop.crop_name).fallback}
                alt={crop.crop_name}
                className="crop-card__image"
              />
              <div className="crop-card__overlay">
                <span className="crop-card__position">#{idx + 1}</span>
              </div>
            </div>

            <div className="crop-card__content">
              <div className="crop-card__header">
                <div>
                  <h3 className="crop-card__name">{crop.crop_name}</h3>
                  <p className="crop-card__season">{crop.season}</p>
                </div>
                <div 
                  className="crop-card__badge"
                  style={{ backgroundColor: getCropSuitabilityColor(crop.confidence_score) }}
                >
                  {Math.round((crop.confidence_score || 0) * 100)}%
                </div>
              </div>

              <div className="crop-card__metrics">
                <div className="metric">
                  <span className="metric__icon">
                    <span className="material-symbols-outlined">eco</span>
                  </span>
                  <div>
                    <p className="metric__label">{t('dashboard.suitability')}</p>
                    <p className="metric__value" style={{ color: getCropSuitabilityColor(crop.confidence_score) }}>
                      {t(`dashboard.${getCropSuitabilityLabel(crop.confidence_score).toLowerCase()}`)}
                    </p>
                  </div>
                </div>

                <div className="metric">
                  <span className="metric__icon">
                    <span className="material-symbols-outlined">calendar_today</span>
                  </span>
                  <div>
                    <p className="metric__label">{t('dashboard.season')}</p>
                    <p className="metric__value">{crop.season?.split('(')[0].trim()}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedCrop && (
        <div className="crop-details">
          <div className="crop-details__header">
            <h3>{selectedCrop.crop_name} - {t('dashboard.detailedAnalysis')}</h3>
          </div>

          <div className="crop-details__grid">
            <div className="detail-card detail-card--primary">
              <div className="detail-card__icon" style={{ background: getCropSuitabilityColor(selectedCrop.confidence_score) }}>
                <span className="material-symbols-outlined">verified_user</span>
              </div>
              <h4>{t('dashboard.overallSuitability')}</h4>
              <p className="detail-card__value">
                {t(`dashboard.${getCropSuitabilityLabel(selectedCrop.confidence_score).toLowerCase()}`)}
              </p>
              <p className="detail-card__desc">
                {Math.round((selectedCrop.confidence_score || 0) * 100)}% {t('dashboard.match')}
              </p>
            </div>

            {selectedCrop.suitability_factors && (
              <>
                {Object.entries(selectedCrop.suitability_factors).map(([factor, score]) => (
                  <div key={factor} className="detail-card">
                    <div className="detail-card__header-row">
                      <h4 className="detail-card__factor-name">
                        {factor.charAt(0).toUpperCase() + factor.slice(1)}
                      </h4>
                      <p className="detail-card__value">{Math.round(score * 100)}%</p>
                    </div>
                    <div className="detail-card__bar">
                      <div className="detail-card__bar-fill" style={{ width: `${score * 100}%` }} />
                    </div>
                  </div>
                ))}
              </>
            )}

            {gisData && (
              <div className="detail-card detail-card--highlight">
                <span className="material-symbols-outlined" style={{ fontSize: '1.5rem', color: '#4CAF50' }}>
                  location_on
                </span>
                <h4>{t('dashboard.gisAnalysis')}</h4>
                <p className="detail-card__desc">
                  {t('dashboard.basedOnGis')}
                </p>
              </div>
            )}

            <div className="detail-card">
              <span className="material-symbols-outlined" style={{ fontSize: '1.5rem', color: '#673AB7' }}>
                calendar_today
              </span>
              <h4>{t('dashboard.growingSeason')}</h4>
              <p className="detail-card__value">
                {selectedCrop.season || '6-8 months'}
              </p>
            </div>
          </div>

          {selectedCrop.reasoning && (
            <div className="crop-details__reasoning">
              <h4>{t('dashboard.recommendation')}</h4>
              <p>{selectedCrop.reasoning}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
