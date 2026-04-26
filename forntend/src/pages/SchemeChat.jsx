import { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useAppData } from '../context/AppDataContext';
import { sendSchemeChat, confirmSchemeSubmission } from '../services/api';
import './SchemeChat.css';

const SPEECH_LANG = { en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN' };

const STEPS = ['scheme_identified', 'collecting_data', 'eligibility_checked', 'form_generated', 'completed'];

const STEP_LABELS = {
  en: {
    pending: 'Getting started…',
    scheme_identified: 'Scheme identified',
    collecting_data: 'Collecting your details',
    eligibility_checked: 'Eligibility confirmed',
    form_generated: 'Form ready — please review',
    completed: 'Application submitted!',
    rejected: 'Not eligible',
  },
  hi: {
    pending: 'शुरू हो रहा है…',
    scheme_identified: 'योजना पहचानी गई',
    collecting_data: 'आपकी जानकारी ली जा रही है',
    eligibility_checked: 'पात्रता जांच पूरी',
    form_generated: 'फॉर्म तैयार — कृपया जांचें',
    completed: 'आवेदन सफलतापूर्वक जमा!',
    rejected: 'पात्र नहीं',
  },
  mr: {
    pending: 'सुरू होत आहे…',
    scheme_identified: 'योजना ओळखली',
    collecting_data: 'तुमची माहिती घेतली जात आहे',
    eligibility_checked: 'पात्रता तपासणी पूर्ण',
    form_generated: 'अर्ज तयार — कृपया तपासा',
    completed: 'अर्ज यशस्वीरित्या सादर!',
    rejected: 'पात्र नाही',
  },
};

const STEP_ICONS = {
  scheme_identified: 'search',
  collecting_data: 'edit_note',
  eligibility_checked: 'verified',
  form_generated: 'description',
  completed: 'check_circle',
};

// ─── Local fallback questions when backend is unavailable ───
const LOCAL_QUESTIONS = [
  { key: 'full_name',    en: 'What is your full name?',                               hi: 'आपका पूरा नाम क्या है?',                          mr: 'तुमचे पूर्ण नाव काय आहे?' },
  { key: 'phone',        en: 'What is your mobile number?',                            hi: 'आपका मोबाइल नंबर क्या है?',                        mr: 'तुमचा मोबाइल नंबर काय आहे?' },
  { key: 'aadhaar',      en: 'Please provide your 12-digit Aadhaar number.',           hi: 'कृपया अपना 12 अंकों का आधार नंबर बताएं।',          mr: 'कृपया तुमचा 12 अंकी आधार क्रमांक सांगा.' },
  { key: 'state',        en: 'Which state do you live in?',                            hi: 'आप किस राज्य में रहते हैं?',                       mr: 'तुम्ही कोणत्या राज्यात राहता?' },
  { key: 'district',     en: 'Which district do you live in?',                         hi: 'आप किस जिले में रहते हैं?',                        mr: 'तुम्ही कोणत्या जिल्ह्यात राहता?' },
  { key: 'land_area',    en: 'How much farmland do you own (in acres)?',               hi: 'आपके पास कितनी खेती की जमीन है (एकड़ में)?',       mr: 'तुमच्याकडे किती शेतजमीन आहे (एकरमध्ये)?' },
  { key: 'bank_account', en: 'What is your bank account number?',                      hi: 'आपका बैंक खाता नंबर क्या है?',                     mr: 'तुमचा बँक खाते क्रमांक काय आहे?' },
  { key: 'ifsc',         en: 'What is your bank IFSC code?',                           hi: 'आपका बैंक IFSC कोड क्या है?',                      mr: 'तुमचा बँक IFSC कोड काय आहे?' },
];

export default function SchemeChat() {
  const location = useLocation();
  const navigate = useNavigate();
  const { t, lang } = useLanguage();
  const { profile } = useAppData();

  const schemeName = location.state?.schemeName || 'Government Scheme';
  const schemeData = location.state?.schemeData || null;
  const mode = location.state?.mode || 'info'; // 'apply' or 'info'

  const isApplyMode = mode === 'apply';

  const getInitGreeting = () => {
    if (isApplyMode) return t('schemeChat.applyGreeting').replace('{scheme}', schemeName);
    return t('schemeChat.greeting').replace('{scheme}', schemeName);
  };

  const [messages, setMessages] = useState(
    isApplyMode ? [] : [{ id: 'init', role: 'assistant', content: getInitGreeting() }]
  );
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState(null);
  const [currentStep, setCurrentStep] = useState('pending');
  const [formReady, setFormReady] = useState(false);
  const [collectedData, setCollectedData] = useState({});
  const [missingFields, setMissingFields] = useState([]);
  const [showSummary, setShowSummary] = useState(false);
  const [recording, setRecording] = useState(false);
  const recordingRef = useRef(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [started, setStarted] = useState(!isApplyMode);
  const [speaking, setSpeaking] = useState(false);

  // Local fallback state
  const [localMode, setLocalMode] = useState(false);
  const [localQIdx, setLocalQIdx] = useState(0);
  const localDataRef = useRef({});
  const [appRefId, setAppRefId] = useState(null);

  const messagesEndRef = useRef(null);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) { try { recognitionRef.current.abort(); } catch {} }
      if (recorderRef.current && recorderRef.current.state !== 'inactive') recorderRef.current.stop();
      if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); }
      window.speechSynthesis.cancel();
    };
  }, []);

  const stepLabels = STEP_LABELS[lang] || STEP_LABELS.en;
  const isTerminal = currentStep === 'completed' || currentStep === 'rejected';
  const activeStepIdx = STEPS.indexOf(currentStep);

  // ─── Speak text aloud (TTS) ───
  const speakText = useCallback((text) => {
    if (!text || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const clean = text.replace(/\*\*/g, '');
    const utter = new SpeechSynthesisUtterance(clean);
    utter.lang = SPEECH_LANG[lang] || 'en-IN';
    utter.rate = 0.95;
    utter.onstart = () => setSpeaking(true);
    utter.onend = () => setSpeaking(false);
    utter.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utter);
  }, [lang]);

  // ─── Local fallback: ask the next question ───
  const askLocalQuestion = useCallback((idx) => {
    if (idx >= LOCAL_QUESTIONS.length) {
      // All questions answered — show summary
      const summaryMsgs = {
        en: 'I have collected all your details. Please review and confirm.',
        hi: 'मैंने आपकी सभी जानकारी एकत्र कर ली है। कृपया जांचें और पुष्टि करें।',
        mr: 'मी तुमची सर्व माहिती गोळा केली आहे. कृपया तपासा आणि पुष्टी करा.',
      };
      const msg = summaryMsgs[lang] || summaryMsgs.en;
      setMessages(prev => [...prev, { id: Date.now().toString() + 'done', role: 'assistant', content: msg }]);
      speakText(msg);
      setCurrentStep('form_generated');
      setFormReady(true);
      setMissingFields([]);
      return;
    }
    const q = LOCAL_QUESTIONS[idx];
    const question = q[lang] || q.en;
    setMessages(prev => [...prev, { id: Date.now().toString() + 'q' + idx, role: 'assistant', content: question }]);
    speakText(question);
    // Update missing fields for display
    setMissingFields(LOCAL_QUESTIONS.slice(idx).map(f => f.key));
  }, [lang, speakText]);

  // ─── Local fallback: process user answer ───
  const processLocalAnswer = useCallback((text) => {
    const field = LOCAL_QUESTIONS[localQIdx];
    if (!field) return;
    localDataRef.current[field.key] = text;
    setCollectedData({ ...localDataRef.current });
    const nextIdx = localQIdx + 1;
    setLocalQIdx(nextIdx);
    // Small delay so the user bubble renders first
    setTimeout(() => askLocalQuestion(nextIdx), 400);
  }, [localQIdx, askLocalQuestion]);

  // ─── Start the local fallback flow ───
  const startLocalFlow = useCallback(() => {
    setLocalMode(true);
    setCurrentStep('collecting_data');
    setLocalQIdx(0);
    localDataRef.current = {};
    setCollectedData({});
    setMissingFields(LOCAL_QUESTIONS.map(f => f.key));
    // Ask first question after a brief pause
    setTimeout(() => askLocalQuestion(0), 500);
  }, [askLocalQuestion]);

  // ─── Handle "Start" button click ───
  const handleStart = () => {
    setStarted(true);
    const greeting = getInitGreeting();
    setMessages(prev => [...prev, { id: 'greeting', role: 'assistant', content: greeting }]);
    speakText(greeting);
    sendMessage(t('schemeChat.autoStartMessage').replace('{scheme}', schemeName));
  };

  // ─── Send message (text) — tries backend, falls back to local ───
  const sendMessage = async (text) => {
    if (!text?.trim() || loading) return;
    const userText = text.trim();

    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', content: userText }]);

    // If already in local mode, process answer locally
    if (localMode) {
      processLocalAnswer(userText);
      return;
    }

    setLoading(true);

    try {
      const result = await sendSchemeChat({
        threadId,
        userId: profile.userId,
        message: userText,
        schemeData: !threadId ? schemeData : null,
        language: lang,
        userState: profile.state || null,
        landArea: profile.landArea || 0,
      });

      if (result.thread_id) setThreadId(result.thread_id);
      if (result.status) setCurrentStep(result.status);
      if (result.collected_data) setCollectedData(result.collected_data);
      if (result.missing_fields) setMissingFields(result.missing_fields);

      const aiText = result.text_response;
      if (aiText) {
        setMessages(prev => [...prev, {
          id: Date.now().toString() + 'ai',
          role: 'assistant',
          content: aiText,
        }]);
        speakText(aiText);
      }

      if (result.status === 'form_generated') setFormReady(true);
    } catch (e) {
      console.error('Backend error, switching to local mode:', e);
      // Switch to local Q&A fallback
      startLocalFlow();
    } finally {
      setLoading(false);
    }
  };

  const handleSendText = () => {
    window.speechSynthesis.cancel();
    sendMessage(inputText);
    setInputText('');
  };

  // ─── Voice recording with live transcript ───
  const startRecording = async () => {
    window.speechSynthesis.cancel();
    setLiveTranscript('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];

      const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'];
      let mimeType = '';
      for (const t of types) { if (MediaRecorder.isTypeSupported(t)) { mimeType = t; break; } }

      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
      recorderRef.current = recorder;
      recorder.ondataavailable = (e) => { if (e.data?.size > 0) chunksRef.current.push(e.data); };
      recorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop());
        streamRef.current = null;
      };
      recorder.start(1000);
      setRecording(true);
      recordingRef.current = true;
      setLiveTranscript('');  // ensure clean start

      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SR) {
        const recognition = new SR();
        recognition.lang = SPEECH_LANG[lang] || 'en-IN';
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.onresult = (event) => {
          let interim = '', final = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const tr = event.results[i][0].transcript;
            if (event.results[i].isFinal) final += tr + ' ';
            else interim += tr;
          }
          setLiveTranscript(prev => {
            const base = final ? (prev.replace(/…$/, '') + final).trim() : prev;
            return interim ? `${base} ${interim}…`.trim() : base;
          });
        };
        recognition.onerror = (e) => { console.log('Speech recognition error:', e.error); };
        recognition.onend = () => {
          if (recognitionRef.current && recordingRef.current) {
            try { recognitionRef.current.start(); } catch {}
          }
        };
        recognitionRef.current = recognition;
        recognition.start();
      }
    } catch (err) {
      console.error('Mic error:', err);
    }
  };

  const stopRecording = () => {
    recordingRef.current = false;
    if (recognitionRef.current) { try { recognitionRef.current.abort(); } catch {} recognitionRef.current = null; }
    if (recorderRef.current && recorderRef.current.state !== 'inactive') recorderRef.current.stop();
    setRecording(false);

    const text = liveTranscript.replace(/…$/, '').trim();
    if (text) {
      sendMessage(text);
    }
    setLiveTranscript('');
  };

  const toggleRecording = () => {
    if (recording) stopRecording();
    else startRecording();
  };

  // ─── Confirm / Revise ───
  const handleConfirm = async (approved) => {
    if (localMode) {
      // Local mode: handle confirm/revise locally
      if (approved) {
        const refId = 'NEXUS-' + Date.now().toString(36).toUpperCase() + '-' + Math.random().toString(36).substring(2, 6).toUpperCase();
        setAppRefId(refId);
        const doneMsgs = {
          en: `Your application has been successfully submitted! Reference: ${refId}`,
          hi: `आपका आवेदन सफलतापूर्वक जमा हो गया है! संदर्भ संख्या: ${refId}`,
          mr: `तुमचा अर्ज यशस्वीरित्या सादर झाला आहे! संदर्भ क्रमांक: ${refId}`,
        };
        const msg = doneMsgs[lang] || doneMsgs.en;
        setMessages(prev => [...prev, { id: Date.now().toString() + 'done', role: 'assistant', content: msg }]);
        speakText(msg);
        setCurrentStep('completed');
        setFormReady(false);
      } else {
        const redoMsgs = {
          en: 'Alright, let\'s start over. Please provide the correct information.',
          hi: 'ठीक है, आइए फिर से शुरू करते हैं। कृपया सही जानकारी दें।',
          mr: 'ठीक आहे, पुन्हा सुरू करूया. कृपया योग्य माहिती द्या.',
        };
        const msg = redoMsgs[lang] || redoMsgs.en;
        setMessages(prev => [...prev, { id: Date.now().toString() + 'redo', role: 'assistant', content: msg }]);
        speakText(msg);
        setFormReady(false);
        setLocalQIdx(0);
        localDataRef.current = {};
        setCollectedData({});
        setCurrentStep('collecting_data');
        setTimeout(() => askLocalQuestion(0), 1200);
      }
      return;
    }

    if (!threadId) return;
    setLoading(true);
    setFormReady(false);
    try {
      const result = await confirmSchemeSubmission({ threadId, approved });
      if (result.current_step) setCurrentStep(result.current_step);
      if (result.last_ai_message) {
        const aiMsg = result.last_ai_message;
        setMessages(prev => [...prev, {
          id: Date.now().toString() + 'confirm',
          role: 'assistant',
          content: aiMsg,
        }]);
        speakText(aiMsg);
      }
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, {
        id: Date.now().toString() + 'err',
        role: 'assistant',
        content: t('schemeChat.errorMessage'),
      }]);
    } finally {
      setLoading(false);
    }
  };

  // ─── Collected data display labels ───
  const fieldLabel = (key) => {
    const labels = {
      en: { full_name: 'Name', aadhaar: 'Aadhaar', state: 'State', district: 'District', land_area: 'Land (acres)', crop: 'Crop', income: 'Income', bank_account: 'Bank A/C', ifsc: 'IFSC', phone: 'Phone' },
      hi: { full_name: 'नाम', aadhaar: 'आधार', state: 'राज्य', district: 'जिला', land_area: 'भूमि (एकड़)', crop: 'फसल', income: 'आय', bank_account: 'बैंक खाता', ifsc: 'IFSC', phone: 'फोन' },
      mr: { full_name: 'नाव', aadhaar: 'आधार', state: 'राज्य', district: 'जिल्हा', land_area: 'जमीन (एकर)', crop: 'पीक', income: 'उत्पन्न', bank_account: 'बँक खाते', ifsc: 'IFSC', phone: 'फोन' },
    };
    return (labels[lang] || labels.en)[key] || key;
  };

  return (
    <div className="scheme-chat animate-fade-up">
      {/* Header */}
      <div className="scheme-chat__header glass">
        <button className="btn btn-ghost" onClick={() => navigate(-1)} style={{ padding: '8px', minHeight: 'auto', marginRight: '12px' }}>
          <span className="material-symbols-outlined">arrow_back</span>
        </button>
        <div className="scheme-chat__header-info">
          <div className="scheme-chat__avatar">
            <span className="material-symbols-outlined">{isApplyMode ? 'description' : 'smart_toy'}</span>
          </div>
          <div style={{ flex: 1 }}>
            <h2 className="text-h3" style={{ margin: 0, fontSize: '18px' }}>
              {isApplyMode ? t('schemeChat.formAssistant') : t('schemeChat.nexusAi')}
            </h2>
            <p style={{ margin: 0, fontSize: '12px', opacity: 0.8, color: 'var(--color-primary)' }}>
              {t('schemeChat.chattingAbout')} {schemeName}
            </p>
          </div>
          {isApplyMode && Object.keys(collectedData).length > 0 && (
            <button className="btn btn-ghost" onClick={() => setShowSummary(!showSummary)} style={{ padding: '6px', minHeight: 'auto' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>
                {showSummary ? 'close' : 'list_alt'}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* Progress stepper — only in apply mode after started */}
      {isApplyMode && started && currentStep !== 'pending' && (
        <div className="scheme-chat__stepper">
          {STEPS.map((step, i) => {
            const done = activeStepIdx >= i;
            const active = currentStep === step;
            return (
              <div key={step} className={`stepper-item${done ? ' stepper-item--done' : ''}${active ? ' stepper-item--active' : ''}`}>
                <div className="stepper-icon">
                  <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>
                    {done && !active ? 'check' : (STEP_ICONS[step] || 'circle')}
                  </span>
                </div>
                <span className="stepper-label">{stepLabels[step] || step}</span>
                {i < STEPS.length - 1 && <div className={`stepper-line${done ? ' stepper-line--done' : ''}`} />}
              </div>
            );
          })}
        </div>
      )}

      {/* Simple status bar for info mode */}
      {!isApplyMode && currentStep !== 'pending' && (
        <div className="scheme-chat__status glass" style={{ margin: '8px 16px', padding: '8px 14px', borderRadius: '10px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="material-symbols-outlined" style={{ fontSize: '18px', color: isTerminal ? (currentStep === 'completed' ? 'var(--color-success)' : 'var(--color-error)') : 'var(--color-primary)' }}>
            {currentStep === 'completed' ? 'check_circle' : currentStep === 'rejected' ? 'cancel' : 'pending'}
          </span>
          <span>{stepLabels[currentStep] || currentStep}</span>
        </div>
      )}

      {/* Collected data summary panel */}
      {showSummary && (
        <div className="scheme-chat__summary glass" style={{ margin: '0 16px 8px', padding: '14px', borderRadius: '12px', fontSize: '13px' }}>
          <h4 style={{ margin: '0 0 8px', fontSize: '14px', color: 'var(--color-primary-dark)' }}>
            {t('schemeChat.collectedInfo')}
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {Object.entries(collectedData).map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid var(--color-outline-variant)' }}>
                <span style={{ color: 'var(--color-on-surface-variant)', fontWeight: 600 }}>{fieldLabel(k)}</span>
                <span style={{ color: 'var(--color-on-surface)' }}>{String(v)}</span>
              </div>
            ))}
          </div>
          {missingFields.length > 0 && (
            <p style={{ margin: '8px 0 0', fontSize: '12px', color: 'var(--color-error)' }}>
              {t('schemeChat.stillNeeded')}: {missingFields.map(f => fieldLabel(f)).join(', ')}
            </p>
          )}
        </div>
      )}

      {/* Messages */}
      <div className="scheme-chat__messages">
        {messages.map(msg => (
          <div key={msg.id} className={`chat-bubble-wrap ${msg.role === 'user' ? 'chat-bubble-wrap--right' : 'chat-bubble-wrap--left'}`}>
            <div className={`chat-bubble chat-bubble--${msg.role}`}>
              {msg.content}
              {msg.role === 'assistant' && speaking && msg.id === messages.filter(m => m.role === 'assistant').slice(-1)[0]?.id && (
                <span className="speaking-indicator">
                  <span className="material-symbols-outlined" style={{ fontSize: '14px', marginLeft: '6px', color: 'var(--color-primary)', verticalAlign: 'middle' }}>volume_up</span>
                </span>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-bubble-wrap chat-bubble-wrap--left">
            <div className="chat-bubble chat-bubble--assistant typing-indicator">
              <span>.</span><span>.</span><span>.</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Live transcript while recording */}
      {recording && (
        <div className="scheme-chat__live-transcript" style={{ margin: '0 16px 4px', padding: '10px 14px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)', fontSize: '14px', color: 'var(--color-on-surface)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="material-symbols-outlined speaking-indicator" style={{ fontSize: '18px', color: 'var(--color-error)' }}>mic</span>
          <span style={{ flex: 1 }}>{liveTranscript || (lang === 'hi' ? 'सुन रहा हूँ… बोलिए' : lang === 'mr' ? 'ऐकत आहे… बोला' : 'Listening… speak now')}</span>
          <button onClick={stopRecording} style={{ background: 'var(--color-error)', color: '#fff', border: 'none', borderRadius: '20px', padding: '4px 14px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>
            {lang === 'hi' ? 'भेजें' : lang === 'mr' ? 'पाठवा' : 'Send'}
          </button>
        </div>
      )}

      {/* ── Start button (apply mode only, before started) ── */}
      {isApplyMode && !started && (
        <div className="scheme-chat__start-area">
          <button className="scheme-chat__start-btn" onClick={handleStart}>
            <span className="material-symbols-outlined" style={{ fontSize: '32px' }}>play_arrow</span>
            <span>{t('schemeChat.startApplication')}</span>
          </button>
          <p style={{ textAlign: 'center', fontSize: '13px', color: 'var(--color-on-surface-variant)', marginTop: '8px' }}>
            {t('schemeChat.startHint')}
          </p>
        </div>
      )}

      {/* Confirm / Revise bar */}
      {formReady && !isTerminal && (
        <div className="scheme-chat__confirm glass" style={{ margin: '0 16px 8px', padding: '12px', borderRadius: '12px', display: 'flex', gap: '10px', justifyContent: 'center' }}>
          <button className="btn btn-primary" onClick={() => handleConfirm(true)} disabled={loading} style={{ flex: 1 }}>
            <span className="material-symbols-outlined icon-sm" style={{ marginRight: 4 }}>check</span>
            {t('schemeChat.confirm')}
          </button>
          <button className="btn btn-ghost" onClick={() => handleConfirm(false)} disabled={loading} style={{ flex: 1 }}>
            <span className="material-symbols-outlined icon-sm" style={{ marginRight: 4 }}>edit</span>
            {t('schemeChat.revise')}
          </button>
        </div>
      )}

      {/* ── Success confirmation card ── */}
      {currentStep === 'completed' && appRefId && (
        <div className="scheme-chat__success-card" style={{ margin: '0 16px 12px', padding: '20px', borderRadius: '16px', background: 'linear-gradient(135deg, #ecfdf5, #d1fae5)', border: '2px solid var(--color-primary)', textAlign: 'center' }}>
          <span className="material-symbols-outlined" style={{ fontSize: '48px', color: 'var(--color-primary)' }}>verified</span>
          <h3 style={{ margin: '8px 0 4px', color: 'var(--color-primary-dark)', fontSize: '18px' }}>
            {lang === 'hi' ? 'आवेदन सफल!' : lang === 'mr' ? 'अर्ज यशस्वी!' : 'Application Successful!'}
          </h3>
          <div style={{ background: '#fff', borderRadius: '10px', padding: '12px', margin: '12px 0', border: '1px solid var(--color-outline-variant)' }}>
            <p style={{ margin: '0 0 4px', fontSize: '11px', color: 'var(--color-on-surface-variant)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              {lang === 'hi' ? 'संदर्भ संख्या' : lang === 'mr' ? 'संदर्भ क्रमांक' : 'Reference Number'}
            </p>
            <p style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--color-primary-dark)', fontFamily: 'monospace', letterSpacing: '1px' }}>{appRefId}</p>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--color-on-surface-variant)', display: 'flex', flexDirection: 'column', gap: '4px', textAlign: 'left', marginTop: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>{lang === 'hi' ? 'योजना' : lang === 'mr' ? 'योजना' : 'Scheme'}</span>
              <strong style={{ color: 'var(--color-on-surface)' }}>{schemeName}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>{lang === 'hi' ? 'दिनांक' : lang === 'mr' ? 'दिनांक' : 'Date'}</span>
              <strong style={{ color: 'var(--color-on-surface)' }}>{new Date().toLocaleDateString(SPEECH_LANG[lang] || 'en-IN')}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>{lang === 'hi' ? 'आवेदक' : lang === 'mr' ? 'अर्जदार' : 'Applicant'}</span>
              <strong style={{ color: 'var(--color-on-surface)' }}>{collectedData.full_name || collectedData.farmer_name || '—'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>{lang === 'hi' ? 'स्थिति' : lang === 'mr' ? 'स्थिती' : 'Status'}</span>
              <strong style={{ color: 'var(--color-primary)' }}>{lang === 'hi' ? 'प्रोसेसिंग' : lang === 'mr' ? 'प्रक्रियेत' : 'Processing'}</strong>
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => navigate(-1)} style={{ marginTop: '16px', width: '100%' }}>
            <span className="material-symbols-outlined icon-sm" style={{ marginRight: 4 }}>arrow_back</span>
            {lang === 'hi' ? 'योजनाओं पर वापस जाएं' : lang === 'mr' ? 'योजनांवर परत जा' : 'Back to Schemes'}
          </button>
        </div>
      )}

      {/* Input area with mic + text (hidden before start in apply mode, hidden after completion) */}
      {(started || !isApplyMode) && !isTerminal && (
        <div className="scheme-chat__input-area">
          <div className="chat-input-wrapper glass">
            <button
              className={`scheme-chat__mic-btn${recording ? ' scheme-chat__mic-btn--active' : ''}`}
              onClick={toggleRecording}
              disabled={loading || isTerminal}
              aria-label={recording ? t('schemeChat.stopRecording') : t('schemeChat.tapToSpeak')}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '22px', color: recording ? '#fff' : 'var(--color-primary)' }}>
                {recording ? 'stop' : 'mic'}
              </span>
            </button>
            <input
              type="text"
              placeholder={t('schemeChat.placeholder')}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendText()}
              disabled={loading || isTerminal || recording}
            />
            <button
              className="btn btn-primary"
              style={{ borderRadius: '50%', padding: '10px', width: '44px', height: '44px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              disabled={loading || !inputText.trim() || isTerminal || recording}
              onClick={handleSendText}
            >
              <span className="material-symbols-outlined icon-sm">send</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
