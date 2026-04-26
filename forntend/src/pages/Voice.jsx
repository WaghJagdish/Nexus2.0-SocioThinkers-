import { useEffect, useRef, useState, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useAppData } from '../context/AppDataContext';
import { useLanguage } from '../context/LanguageContext';
import CropRecommendations from '../components/CropRecommendations';
import './Voice.css';

const WAVE_HEIGHTS = [12, 16, 8, 20, 24, 14, 18, 22, 10, 16, 24, 12, 8, 16, 20, 14, 10, 22, 16, 12];

// Map app language codes to Web Speech API / BCP-47 locale tags
const SPEECH_LANG_MAP = {
  en: 'en-IN',
  hi: 'hi-IN',
  mr: 'mr-IN',
};

export default function Voice() {
  const { t, lang } = useLanguage();
  const location = useLocation();
  const { runVoiceQuery, runTextQuery, status, documentUrl, profile } = useAppData();
  const [listening, setListening] = useState(false);
  const [message, setMessage] = useState('');
  const [text, setText] = useState(location.state?.initialText || '');
  const [waveHeights, setWaveHeights] = useState(WAVE_HEIGHTS);
  const [sessionResult, setSessionResult] = useState(null);
  const [liveTranscript, setLiveTranscript] = useState('');
  const intervalRef = useRef(null);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (location.state?.initialText) {
      setText(location.state.initialText);
    }
  }, [location.state?.initialText]);

  useEffect(() => {
    if (listening) {
      intervalRef.current = setInterval(() => {
        setWaveHeights(WAVE_HEIGHTS.map(() => 8 + Math.random() * 56));
      }, 120);
    } else {
      clearInterval(intervalRef.current);
      setWaveHeights(WAVE_HEIGHTS);
    }
    return () => clearInterval(intervalRef.current);
  }, [listening]);

  // Cleanup on unmount: stop recording and release mic
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch { /* ignore */ }
        recognitionRef.current = null;
      }
      if (recorderRef.current && recorderRef.current.state !== 'inactive') {
        recorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, []);

  // --- Live Speech Recognition (Web Speech API) ---
  const startSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return; // gracefully degrade

    const recognition = new SpeechRecognition();
    recognition.lang = SPEECH_LANG_MAP[lang] || 'en-IN';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript + ' ';
        } else {
          interim += transcript;
        }
      }
      setLiveTranscript((prev) => {
        const base = final ? (prev.replace(/…$/, '') + final).trim() : prev;
        return interim ? `${base} ${interim}…`.trim() : base;
      });
    };

    recognition.onerror = (event) => {
      // 'no-speech' is normal if user hasn't spoken yet
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        console.warn('SpeechRecognition error:', event.error);
      }
    };

    recognition.onend = () => {
      // Auto-restart if still listening (browser may stop it)
      if (recognitionRef.current && listening) {
        try { recognitionRef.current.start(); } catch { /* already running */ }
      }
    };

    recognitionRef.current = recognition;
    try { recognition.start(); } catch { /* ignore */ }
  };

  const stopSpeechRecognition = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch { /* ignore */ }
      recognitionRef.current = null;
    }
  };

  const getSupportedMimeType = () => {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/mp4',
      'audio/wav',
    ];
    for (const t of types) {
      if (MediaRecorder.isTypeSupported(t)) return t;
    }
    return '';
  };

  const startRecording = async () => {
    setMessage('');
    setSessionResult(null);
    setLiveTranscript('');
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setMessage(t('voice.micNotSupported'));
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];

      const mimeType = getSupportedMimeType();
      const options = mimeType ? { mimeType } : {};
      const recorder = new MediaRecorder(stream, options);
      recorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        if (chunksRef.current.length === 0) {
          setMessage(t('voice.micNotSupported'));
          return;
        }

        const blobType = recorder.mimeType || mimeType || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type: blobType });

        if (blob.size < 100) {
          setMessage(t('voice.micNotSupported'));
          return;
        }

        try {
          const result = await runVoiceQuery(blob, location.state?.initialText);
          setSessionResult(result);
          setMessage(t('voice.completed'));
        } catch (error) {
          setMessage(error.message);
        }
      };

      recorder.onerror = (event) => {
        console.error('MediaRecorder error:', event.error);
        setMessage(event.error?.message || t('voice.micNotSupported'));
        setListening(false);
      };

      // Use timeslice (1s chunks) so ondataavailable fires during recording
      recorder.start(1000);
      setListening(true);
      startSpeechRecognition();
    } catch (error) {
      console.error('getUserMedia error:', error);
      setMessage(error.message || t('voice.micNotSupported'));
    }
  };

  const stopRecording = () => {
    stopSpeechRecognition();
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop();
    }
    setListening(false);
  };

  const toggleListen = () => {
    if (listening) stopRecording();
    else startRecording();
  };

  const submitText = async () => {
    if (!text.trim()) return;
    setMessage('');
    setSessionResult(null);
    try {
      const result = await runTextQuery(text.trim());
      setSessionResult(result);
      setText('');
      setMessage(t('voice.textCompleted'));
    } catch (error) {
      setMessage(error.message);
    }
  };

  const audioUrl = sessionResult?.response_audio_url?.startsWith('data:')
    ? sessionResult.response_audio_url
    : sessionResult?.response_audio_url
      ? documentUrl(sessionResult.response_audio_url)
      : '';

  return (
    <div className="voice-page animate-fade-up">
      <div className="voice-status">
        <p className="text-h3" style={{ color: 'var(--color-on-surface-variant)', opacity: 0.8 }}>{t('voice.title')}</p>
        <h1 className="text-h2">{listening ? t('voice.subtitle') : t('voice.tapToSpeak')}</h1>
        <p className="text-body-md voice-hint" style={status.error ? { color: 'var(--color-error)' } : undefined}>
          {status.loading ? status.message : status.error ? status.error : message || t('voice.hint')}
        </p>
      </div>

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
          disabled={status.loading && !listening}
        >
          <span className="material-symbols-outlined icon-fill" style={{ fontSize: 64, color: 'white' }}>
            {listening ? 'stop_circle' : 'mic'}
          </span>
        </button>
      </div>

      <div className="voice-transcript glass">
        <div className="voice-transcript__live">
          {listening && <div className="voice-live-dot" />}
          {listening && liveTranscript ? (
            <div>
              <p className="text-body-sm" style={{ color: 'var(--color-primary)', marginBottom: 4, fontWeight: 600 }}>
                {t('voice.liveTranscript')}
              </p>
              <p className="text-body-md" style={{ color: 'var(--color-on-surface)' }}>
                {liveTranscript}
              </p>
            </div>
          ) : status.loading ? (
            <p className="text-body-md" style={{ color: 'var(--color-on-surface-variant)' }}>
              {t('voice.processing')}
            </p>
          ) : (
            <p className="text-body-md" style={{ color: 'var(--color-on-surface-variant)' }}>
              {message || status.error || sessionResult?.response_text || t('voice.defaultPrompt')}
            </p>
          )}
        </div>
      </div>

      {audioUrl && (
        <div className="voice-audio-section">
          <h3 className="text-h4" style={{ marginBottom: '12px', color: 'var(--color-on-surface)' }}>{t('voice.responseAudio')}</h3>
          <audio className="voice-audio" src={audioUrl} controls />
        </div>
      )}

      <div className="voice-text-query">
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder={t('voice.textPlaceholder')}
        />
        <button className="btn btn-primary" type="button" onClick={submitText} disabled={status.loading || !text.trim()}>
          <span className="material-symbols-outlined icon icon-sm">send</span>
          {t('voice.send')}
        </button>
      </div>

      <div className="voice-waveform" aria-hidden="true">
        {waveHeights.map((height, index) => (
          <div
            key={index}
            className="voice-waveform__bar"
            style={{
              height: `${height}px`,
              animationDelay: listening ? `${index * 0.06}s` : '0s',
              animation: listening ? 'wave 0.8s ease-in-out infinite alternate' : 'none',
            }}
          />
        ))}
      </div>

      {(sessionResult?.recommendations || sessionResult?.recommended_crop) && (
        <div className="voice-recommendations-section">
          <CropRecommendations
            recommendations={sessionResult.recommendations || (sessionResult.recommended_crop ? [{
              crop_name: sessionResult.recommended_crop,
              confidence_score: 0.9,
              season: 'Local Season',
              reasoning: sessionResult.response_text || '',
            }] : [])}
            gisData={sessionResult.gis_data}
            isLoading={status.loading}
            latitude={profile.latitude}
            longitude={profile.longitude}
          />
        </div>
      )}
    </div>
  );
}
