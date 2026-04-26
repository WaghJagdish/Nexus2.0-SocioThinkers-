import { useEffect, useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import './WeatherCard.css';

export default function WeatherCard({ latitude, longitude, isLoading }) {
  const { t, lang } = useLanguage();
  const [weather, setWeather] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!latitude || !longitude) {
      setWeather(null);
      return;
    }

    const fetchWeather = async () => {
      try {
        const response = await fetch(
          `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto`
        );
        const data = await response.json();

        if (data.current) {
          setWeather({
            current: data.current,
            daily: data.daily,
            timezone: data.timezone,
          });
          setError('');
        }
      } catch (err) {
        setError('Failed to fetch weather');
        console.error(err);
      }
    };

    fetchWeather();
    const interval = setInterval(fetchWeather, 600000); // Update every 10 minutes
    return () => clearInterval(interval);
  }, [latitude, longitude]);

  if (isLoading) {
    return (
      <div className="weather-card weather-card--skeleton">
        <div className="weather-card__skeleton" />
      </div>
    );
  }

  if (error || !weather) {
    return (
      <div className="weather-card weather-card--error">
        <span className="material-symbols-outlined">info</span>
        <p>{error || t('weather.enableLocation')}</p>
      </div>
    );
  }

  const { current, daily } = weather;
  const temp = Math.round(current.temperature_2m);
  const humidity = current.relative_humidity_2m;
  const windSpeed = Math.round(current.wind_speed_10m);
  const precipitation = current.precipitation;

  const getWeatherIcon = (code) => {
    if (code === 0) return { icon: 'wb_sunny', label: t('weather.clear') };
    if (code === 1 || code === 2) return { icon: 'wb_cloud', label: t('weather.cloudy') };
    if (code === 3) return { icon: 'cloud', label: t('weather.overcast') };
    if (code === 45 || code === 48) return { icon: 'cloud', label: t('weather.foggy') };
    if (code === 51 || code === 53 || code === 55) return { icon: 'grain', label: t('weather.drizzle') };
    if (code === 61 || code === 63 || code === 65) return { icon: 'water_drop', label: t('weather.rain') };
    if (code === 71 || code === 73 || code === 75) return { icon: 'ac_unit', label: t('weather.snow') };
    if (code === 80 || code === 81 || code === 82) return { icon: 'cloudy_snowing', label: t('weather.showers') };
    if (code === 85 || code === 86) return { icon: 'ac_unit', label: t('weather.heavySnow') };
    if (code === 95 || code === 96 || code === 99) return { icon: 'flash_on', label: t('weather.thunderstorm') };
    return { icon: 'help', label: t('weather.unknown') };
  };

  const weatherType = getWeatherIcon(current.weather_code);
  const nextDayTemp = daily ? Math.round(daily.temperature_2m_max[1]) : null;
  const nextDayMin = daily ? Math.round(daily.temperature_2m_min[1]) : null;

  return (
    <div className="weather-card">
      <div className="weather-card__header">
        <div className="weather-card__current">
          <div className="weather-card__temp-section">
            <span className="material-symbols-outlined weather-card__icon">
              {weatherType.icon}
            </span>
            <div className="weather-card__temp-main">
              <h3 className="text-h2">{temp}°C</h3>
              <p className="weather-card__condition">{weatherType.label}</p>
            </div>
          </div>
        </div>

        <div className="weather-card__metrics">
          <div className="weather-metric">
            <span className="material-symbols-outlined">water_drop</span>
            <div>
              <p className="weather-metric__label">{t('weather.humidity')}</p>
              <p className="weather-metric__value">{humidity}%</p>
            </div>
          </div>

          <div className="weather-metric">
            <span className="material-symbols-outlined">air</span>
            <div>
              <p className="weather-metric__label">{t('weather.wind')}</p>
              <p className="weather-metric__value">{windSpeed} km/h</p>
            </div>
          </div>

          <div className="weather-metric">
            <span className="material-symbols-outlined">grain</span>
            <div>
              <p className="weather-metric__label">{t('weather.rainfall')}</p>
              <p className="weather-metric__value">{precipitation?.toFixed(1) || 0} mm</p>
            </div>
          </div>
        </div>
      </div>

      {daily && daily.time.slice(1, 4).length > 0 && (
        <div className="weather-card__forecast">
          <h4 className="text-label-caps">{t('weather.forecast')}</h4>
          <div className="forecast-grid">
            {daily.time.slice(1, 4).map((date, idx) => (
              <div key={date} className="forecast-item">
                <p className="forecast-date">
                  {new Date(date).toLocaleDateString(lang === 'hi' ? 'hi-IN' : lang === 'mr' ? 'mr-IN' : 'en-US', { weekday: 'short' })}
                </p>
                <span className="material-symbols-outlined forecast-icon">
                  {getWeatherIcon(daily.weather_code[idx + 1]).icon}
                </span>
                <p className="forecast-temp">
                  {Math.round(daily.temperature_2m_max[idx + 1])}°
                </p>
                <p className="forecast-min">
                  {Math.round(daily.temperature_2m_min[idx + 1])}°
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
