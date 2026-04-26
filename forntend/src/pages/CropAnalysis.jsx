import { useState, useRef, useCallback } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { useAppData } from '../context/AppDataContext';
import { analyzeCropImage } from '../services/api';
import './CropAnalysis.css';

const SPEECH_LANG = { en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN' };

export default function CropAnalysis() {
  const { t, lang } = useLanguage();
  const { profile, health, addToQueue } = useAppData();
  const [image, setImage] = useState(null);
  const [imageBase64, setImageBase64] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [speaking, setSpeaking] = useState(false);
  const fileInputRef = useRef(null);

  const speakText = useCallback((text) => {
    if (!text || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const clean = text.replace(/\*\*/g, '');
    const utter = new SpeechSynthesisUtterance(clean);
    utter.lang = SPEECH_LANG[lang] || 'en-IN';
    utter.rate = 0.9;
    utter.onstart = () => setSpeaking(true);
    utter.onend = () => setSpeaking(false);
    utter.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utter);
  }, [lang]);

  const processFile = (file) => {
    if (!file || !file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      setImage(e.target.result);
      setImageBase64(e.target.result.split(',')[1]);
      setResult(null);
      setError('');
    };
    reader.readAsDataURL(file);
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  const handleCamera = () => {
    fileInputRef.current?.click();
  };

  const handleAnalyze = async () => {
    if (!imageBase64) return;
    setAnalyzing(true);
    setError('');
    try {
      const res = await analyzeCropImage({
        userId: profile.userId,
        imageBase64,
        language: lang,
        latitude: profile.latitude,
        longitude: profile.longitude,
      });
      setResult(res);
      // Auto-speak summary
      const summary = [
        res.crop_type ? `${res.crop_type}.` : '',
        res.health_status,
        res.disease_detected ? `${res.disease_name}. ${res.treatment_recommendation}` : 'Healthy crop.',
        res.harvest_estimate,
        res.market_price_estimate,
      ].filter(Boolean).join(' ');
      speakText(summary);
    } catch (e) {
      console.error(e);
      setError(t('cropAnalysis.error'));
      // Queue for offline retry
      if (!health) {
        addToQueue({
          type: 'crop_analysis',
          imageBase64,
          language: lang,
          reason: t('cropAnalysis.offlineQueued'),
        });
      }
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReset = () => {
    setImage(null);
    setImageBase64(null);
    setResult(null);
    setError('');
    window.speechSynthesis.cancel();
    setSpeaking(false);
  };

  const healthColor = (score) => {
    if (score >= 80) return 'var(--color-success)';
    if (score >= 50) return 'var(--color-warning)';
    return 'var(--color-error)';
  };

  const healthLabel = (score) => {
    if (score >= 80) return lang === 'hi' ? 'स्वस्थ' : lang === 'mr' ? 'निरोगी' : 'Healthy';
    if (score >= 50) return lang === 'hi' ? 'मध्यम' : lang === 'mr' ? 'मध्यम' : 'Moderate';
    return lang === 'hi' ? 'गंभीर' : lang === 'mr' ? 'गंभीर' : 'Critical';
  };

  return (
    <div className="crop-analysis animate-fade-up">
      {/* Header */}
      <div className="crop-analysis__header">
        <h2 className="text-h2" style={{ margin: 0, fontSize: '20px', color: 'var(--color-primary-dark)' }}>
          <span className="material-symbols-outlined" style={{ verticalAlign: 'middle', marginRight: 8 }}>eco</span>
          {t('cropAnalysis.title')}
        </h2>
        <p className="text-body-sm" style={{ margin: '4px 0 0', color: 'var(--color-secondary)' }}>
          {t('cropAnalysis.subtitle')}
        </p>
      </div>

      {/* Image Preview / Upload Area */}
      <div className="crop-analysis__media glass">
        {image ? (
          <div style={{ position: 'relative' }}>
            <img src={image} alt="Crop" className="crop-analysis__preview" />
            {!analyzing && !result && (
              <button
                onClick={handleReset}
                className="btn btn-ghost"
                style={{ position: 'absolute', top: 8, right: 8, padding: '6px', borderRadius: '50%', background: 'rgba(0,0,0,0.5)', color: '#fff' }}
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            )}
          </div>
        ) : (
          <div className="crop-analysis__upload-placeholder">
            <span className="material-symbols-outlined" style={{ fontSize: 56, color: 'var(--color-outline)' }}>photo_camera</span>
            <p style={{ margin: '12px 0 4px', fontWeight: 600, color: 'var(--color-on-surface-variant)' }}>
              {t('cropAnalysis.takePhoto')}
            </p>
            <p style={{ margin: 0, fontSize: '12px', color: 'var(--color-secondary)' }}>
              {t('cropAnalysis.uploadImage')}
            </p>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        {!image && (
          <div style={{ display: 'flex', gap: 12, marginTop: 16, justifyContent: 'center' }}>
            <button className="btn btn-primary" onClick={handleCamera}>
              <span className="material-symbols-outlined">photo_camera</span>
              {t('cropAnalysis.takePhoto')}
            </button>
            <button className="btn btn-ghost" onClick={() => fileInputRef.current?.click()}>
              <span className="material-symbols-outlined">folder_open</span>
              {t('cropAnalysis.uploadImage')}
            </button>
          </div>
        )}
      </div>

      {/* Analyze button */}
      {image && !result && (
        <div style={{ padding: '0 16px', marginTop: 12 }}>
          <button
            className="btn btn-primary"
            style={{ width: '100%', padding: '14px' }}
            onClick={handleAnalyze}
            disabled={analyzing}
          >
            <span className={`material-symbols-outlined${analyzing ? ' animate-spin-slow' : ''}`}>
              {analyzing ? 'sync' : 'biotech'}
            </span>
            {analyzing ? t('cropAnalysis.analyzing') : lang === 'hi' ? 'विश्लेषण करें' : lang === 'mr' ? 'विश्लेषण करा' : 'Analyze Crop'}
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="crop-analysis__error" style={{ margin: '12px 16px', padding: '12px 16px', borderRadius: '12px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: 'var(--color-error)', fontSize: '14px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="material-symbols-outlined">error</span>
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="crop-analysis__results">
          {/* Health score card */}
          <div className="card-glass" style={{ margin: '12px 16px', padding: '20px', textAlign: 'center' }}>
            <div style={{ position: 'relative', width: 140, height: 140, margin: '0 auto' }}>
              <svg viewBox="0 0 140 140" style={{ transform: 'rotate(-90deg)' }}>
                <circle cx="70" cy="70" r="60" fill="none" stroke="#e5e7eb" strokeWidth="10" />
                <circle
                  cx="70" cy="70" r="60" fill="none"
                  stroke={healthColor(result.health_score)}
                  strokeWidth="10"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 60}`}
                  strokeDashoffset={`${2 * Math.PI * 60 * (1 - (result.health_score || 0) / 100)}`}
                  style={{ transition: 'stroke-dashoffset 0.8s ease' }}
                />
              </svg>
              <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: '32px', fontWeight: 800, color: healthColor(result.health_score) }}>{result.health_score || 0}%</span>
                <span style={{ fontSize: '12px', color: 'var(--color-secondary)', textTransform: 'uppercase' }}>{healthLabel(result.health_score)}</span>
              </div>
            </div>
            <h3 style={{ margin: '12px 0 4px', fontSize: '18px', color: 'var(--color-primary-dark)' }}>
              {result.crop_type || (lang === 'hi' ? 'फसल' : lang === 'mr' ? 'पीक' : 'Crop')}
            </h3>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--color-secondary)' }}>
              {result.health_status}
            </p>
          </div>

          {/* Disease / Treatment card */}
          {result.disease_detected && (
            <div className="card-glass" style={{ margin: '0 16px 12px', padding: '16px', borderLeft: `4px solid ${healthColor(result.health_score)}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <span className="material-symbols-outlined" style={{ color: 'var(--color-error)' }}>coronavirus</span>
                <div>
                  <p style={{ margin: 0, fontWeight: 700, fontSize: '15px', color: 'var(--color-error)' }}>{t('cropAnalysis.diseaseDetected')}</p>
                  <p style={{ margin: '2px 0 0', fontSize: '13px', color: 'var(--color-on-surface-variant)' }}>{result.disease_name} — {t('cropAnalysis.confidence')}: {Math.round((result.confidence || 0) * 100)}%</p>
                </div>
              </div>

              <div style={{ background: 'rgba(16,185,129,0.06)', borderRadius: '10px', padding: '12px', marginBottom: 10 }}>
                <p style={{ margin: '0 0 6px', fontSize: '12px', fontWeight: 700, color: 'var(--color-primary-dark)', textTransform: 'uppercase' }}>{t('cropAnalysis.treatment')}</p>
                <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-on-surface)' }}>{result.treatment_recommendation}</p>
              </div>

              <div style={{ background: 'rgba(245,158,11,0.06)', borderRadius: '10px', padding: '12px' }}>
                <p style={{ margin: '0 0 6px', fontSize: '12px', fontWeight: 700, color: 'var(--color-warning-dark)', textTransform: 'uppercase' }}>{t('cropAnalysis.pesticide')}</p>
                <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-on-surface)' }}>{result.pesticide_fertilizer}</p>
              </div>
            </div>
          )}

          {!result.disease_detected && (
            <>
              <div className="card-glass" style={{ margin: '0 16px 12px', padding: '16px', display: 'flex', alignItems: 'center', gap: 12, background: 'linear-gradient(135deg, #ecfdf5, #d1fae5)' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 36, color: 'var(--color-success)' }}>verified</span>
                <div>
                  <p style={{ margin: 0, fontWeight: 700, color: 'var(--color-success)' }}>{t('cropAnalysis.noDisease')}</p>
                  <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--color-secondary)' }}>{result.health_status}</p>
                </div>
              </div>

              {/* Preventive care for healthy crops */}
              {result.pesticide_fertilizer && result.pesticide_fertilizer !== '—' && (
                <div className="card-glass" style={{ margin: '0 16px 12px', padding: '16px', borderLeft: '4px solid var(--color-primary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                    <span className="material-symbols-outlined" style={{ color: 'var(--color-primary)' }}>spa</span>
                    <div>
                      <p style={{ margin: 0, fontWeight: 700, fontSize: '15px', color: 'var(--color-primary-dark)' }}>{lang === 'hi' ? 'सुझाया गया उर्वरक / देखभाल' : lang === 'mr' ? 'सुचवलेले खत / काळजी' : 'Recommended Fertilizer / Care'}</p>
                    </div>
                  </div>
                  <div style={{ background: 'rgba(16,185,129,0.06)', borderRadius: '10px', padding: '12px', marginBottom: 10 }}>
                    <p style={{ margin: '0 0 6px', fontSize: '12px', fontWeight: 700, color: 'var(--color-primary-dark)', textTransform: 'uppercase' }}>{t('cropAnalysis.pesticide')}</p>
                    <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-on-surface)' }}>{result.pesticide_fertilizer}</p>
                  </div>
                  {result.organic_recommendation && result.organic_recommendation !== '—' && (
                    <div style={{ background: 'rgba(16,185,129,0.04)', borderRadius: '10px', padding: '12px' }}>
                      <p style={{ margin: '0 0 6px', fontSize: '12px', fontWeight: 700, color: 'var(--color-success)', textTransform: 'uppercase' }}>{lang === 'hi' ? 'जैविक विकल्प' : lang === 'mr' ? 'सेंद्रिय पर्याय' : 'Organic Option'}</p>
                      <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-on-surface)' }}>{result.organic_recommendation}</p>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* Harvest & Market */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, margin: '0 16px 12px' }}>
            <div className="card-glass" style={{ padding: '14px', textAlign: 'center' }}>
              <span className="material-symbols-outlined" style={{ color: 'var(--color-primary)', fontSize: '28px' }}>event</span>
              <p style={{ margin: '8px 0 2px', fontSize: '12px', fontWeight: 700, color: 'var(--color-secondary)', textTransform: 'uppercase' }}>{t('cropAnalysis.harvestTime')}</p>
              <p style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: 'var(--color-primary-dark)' }}>{result.harvest_estimate || '—'}</p>
            </div>
            <div className="card-glass" style={{ padding: '14px', textAlign: 'center' }}>
              <span className="material-symbols-outlined" style={{ color: 'var(--color-primary)', fontSize: '28px' }}>currency_rupee</span>
              <p style={{ margin: '8px 0 2px', fontSize: '12px', fontWeight: 700, color: 'var(--color-secondary)', textTransform: 'uppercase' }}>{t('cropAnalysis.marketPrice')}</p>
              <p style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: 'var(--color-primary-dark)' }}>{result.market_price_estimate || '—'}</p>
            </div>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: 12, margin: '0 16px 20px' }}>
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleReset}>
              <span className="material-symbols-outlined">add</span>
              {t('cropAnalysis.retry')}
            </button>
            <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => speakText(result.summary || '')} disabled={speaking}>
              <span className="material-symbols-outlined">volume_up</span>
              {speaking ? '...' : t('cropAnalysis.speakResult')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
