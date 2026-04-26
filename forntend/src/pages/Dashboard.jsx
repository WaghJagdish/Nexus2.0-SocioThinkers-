import { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppData } from '../context/AppDataContext';
import { useLanguage } from '../context/LanguageContext';
import WeatherCard from '../components/WeatherCard';
import CropRecommendations from '../components/CropRecommendations';
import GISSuitabilityMap from '../components/GISSuitabilityMap';
import AIAdvisory from '../components/AIAdvisory';
import './Dashboard.css';

export default function Dashboard() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const {
    health,
    latestResult,
    profile,
    status,
    runTextQuery,
    useCurrentLocation,
  } = useAppData();
  const [query, setQuery] = useState('');
  const [locationMessage, setLocationMessage] = useState('');

  const hasLocation = Boolean(profile?.latitude && profile?.longitude);
  const schemes = latestResult?.matched_schemes || [];
  const responseText = latestResult?.response_text || '';

  const autoFetchedRef = useRef(false);

  const requestAnalysis = useCallback(async () => {
    const text = 'Recommend the best crop for my farm using my location and explain any government schemes I can apply for.';
    await runTextQuery(text);
  }, [runTextQuery]);

  useEffect(() => {
    if (hasLocation && !latestResult?.gis_data && !status.loading && !status.error && !autoFetchedRef.current) {
      autoFetchedRef.current = true;
      requestAnalysis();
    }
  }, [hasLocation, latestResult, status, requestAnalysis]);

  const captureLocation = async () => {
    try {
      const coords = await useCurrentLocation();
      setLocationMessage(`${coords.latitude}, ${coords.longitude}`);
      autoFetchedRef.current = true; 
      requestAnalysis();
    } catch (error) {
      setLocationMessage(error.message);
    }
  };

  return (
    <div className="dashboard animate-fade-up">
      <div className="dashboard__hero">
        <div className="gis-card dashboard-status-card">
          <div className="gis-card__overlay dashboard-status-card__overlay">
            <div className="gis-card__location">
              <span className="material-symbols-outlined icon icon-sm" style={{ color: 'white' }}>location_on</span>
              <span className="text-label-caps" style={{ color: 'white' }}>
                {hasLocation ? `${profile.latitude.toFixed(4)}, ${profile.longitude.toFixed(4)}` : t('common.locationNotSet')}
              </span>
            </div>
            <h2 className="text-h2" style={{ color: 'white' }}>{t('dashboard.title')}</h2>
            <p className="text-body-md dashboard-status-card__copy">
              {health ? t('dashboard.connected') : t('dashboard.notConnected')}
            </p>
            <div className="gis-card__badges">
              <button className="gis-badge" type="button" onClick={captureLocation}>
                <span className="gis-badge__dot gis-badge__dot--primary" />
                {t('dashboard.useGps')}
              </button>
              <button className="gis-badge" type="button" onClick={() => navigate('/settings')}>
                <span className="gis-badge__dot gis-badge__dot--light" />
                {t('dashboard.api')}
              </button>
            </div>
          </div>
        </div>

      </div>

      {hasLocation && (
        <div className="dashboard__section">
          <GISSuitabilityMap
            latitude={profile.latitude}
            longitude={profile.longitude}
            gisData={latestResult?.gis_data}
            isLoading={status.loading}
          />
        </div>
      )}

      {hasLocation && (
        <div className="dashboard__section">
          <WeatherCard
            latitude={profile.latitude}
            longitude={profile.longitude}
            isLoading={status.loading}
          />
        </div>
      )}

      <div className="dashboard__section">
        <AIAdvisory
          responseText={responseText}
          isLoading={status.loading}
          onViewDocs={() => navigate('/fields')}
        />
      </div>

      {hasLocation && (
        <div className="dashboard__section">
          <CropRecommendations
            recommendations={latestResult?.recommendations || (latestResult?.recommended_crop ? [{
              crop_name: latestResult.recommended_crop,
              confidence_score: 0.9,
              season: 'Local Season',
              reasoning: latestResult.response_text || '',
            }] : [])}
            gisData={latestResult?.gis_data}
            isLoading={status.loading}
            latitude={profile.latitude}
            longitude={profile.longitude}
          />
        </div>
      )}
    </div>
  );
}
