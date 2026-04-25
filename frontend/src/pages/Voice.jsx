import { useState, useEffect, useRef } from 'react';
import { useLanguage } from '../context/LanguageContext';
import './Voice.css';

const WAVE_HEIGHTS = [12, 16, 8, 20, 24, 14, 18, 22, 10, 16, 24, 12, 8, 16, 20, 14, 10, 22, 16, 12];

export default function Voice() {
  const { t } = useLanguage();
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [waveHeights, setWaveHeights] = useState(WAVE_HEIGHTS);
  const intervalRef = useRef(null);

  // Animate waveform when listening
  useEffect(() => {
    if (listening) {
      intervalRef.current = setInterval(() => {
        setWaveHeights(waveHeights.map(() => 8 + Math.random() * 56));
      }, 120);
    } else {
      clearInterval(intervalRef.current);
      setWaveHeights(WAVE_HEIGHTS);
    }
    return () => clearInterval(intervalRef.current);
  }, [listening]);

  const toggleListen = () => {
    setListening(l => !l);
    if (!listening) setTranscript('');
  };

  return (
    <div className="voice-page animate-fade-up">
      {/* Status text */}
      <div className="voice-status">
        <p className="text-h3" style={{ color: 'var(--color-on-surface-variant)', opacity: 0.8 }}>{t('voice.title')}</p>
        <h1 className="text-h2">{listening ? t('voice.subtitle') : t('voice.tapToSpeak')}</h1>
        <p className="text-body-md voice-hint">{t('voice.hint')}</p>
      </div>

      {/* Ripple & Mic Button */}
      <div className="voice-mic-wrap">
        {listening && (
          <>
            <div className="voice-ripple voice-ripple--1" />
            <div className="voice-ripple voice-ripple--2" />
            <div className="voice-ripple voice-ripple--3" />
          </>
        )}
        <button
          id="mic-button"
          className={`voice-mic-btn${listening ? ' voice-mic-btn--active' : ''}`}
          onClick={toggleListen}
          aria-label={listening ? t('voice.stop') : t('voice.tapToSpeak')}
        >
          <span className="material-symbols-outlined icon-fill" style={{ fontSize: 64, color: 'white' }}>
            {listening ? 'stop_circle' : 'mic'}
          </span>
        </button>
      </div>

      {/* Transcription Card */}
      <div className="voice-transcript glass">
        {listening ? (
          <div className="voice-transcript__live">
            <div className="voice-live-dot" />
            <p className="text-body-md" style={{ color: 'var(--color-on-surface-variant)', fontStyle: 'italic' }}>
              {transcript || t('voice.transcribing')}
            </p>
          </div>
        ) : (
          <p className="text-body-md" style={{ color: 'var(--color-secondary)', opacity: 0.7 }}>
            {t('voice.transcribing')}
          </p>
        )}
      </div>

      {/* Waveform Visualizer */}
      <div className="voice-waveform" aria-hidden="true">
        {waveHeights.map((h, i) => (
          <div
            key={i}
            className="voice-waveform__bar"
            style={{
              height: `${h}px`,
              animationDelay: listening ? `${i * 0.06}s` : '0s',
              animation: listening ? 'wave 0.8s ease-in-out infinite alternate' : 'none',
            }}
          />
        ))}
      </div>
    </div>
  );
}
