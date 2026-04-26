import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { documentUrl, getApiBase, getHealth, listDocuments, sendTextQuery, sendVoiceSync, setApiBase } from '../services/api';
import { useLanguage } from './LanguageContext';

const AppDataContext = createContext();

const DEFAULT_PROFILE = {
  userId: 'farmer-demo-user',
  fullName: '',
  email: '',
  latitude: 0,
  longitude: 0,
};

function readJson(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) || fallback;
  } catch {
    return fallback;
  }
}

export function AppDataProvider({ children }) {
  const { lang } = useLanguage();
  const [apiBase, setApiBaseState] = useState(getApiBase());
  const [profile, setProfileState] = useState(() => readJson('kisansetu_profile', DEFAULT_PROFILE));
  const [latestResult, setLatestResult] = useState(() => readJson('kisansetu_latest_result', null));
  const [documents, setDocuments] = useState([]);
  const [health, setHealth] = useState(null);
  const [pendingQueue, setPendingQueue] = useState(() => readJson('kisansetu_pending_queue', []));
  const [status, setStatus] = useState({ loading: false, error: '', message: '' });

  const updateProfile = useCallback((patch) => {
    setProfileState((current) => {
      const next = { ...current, ...patch };
      localStorage.setItem('kisansetu_profile', JSON.stringify(next));
      return next;
    });
  }, []);

  const updateApiBase = useCallback((value) => {
    setApiBase(value);
    setApiBaseState(getApiBase());
  }, []);

  const refreshHealth = useCallback(async () => {
    try {
      const result = await getHealth();
      setHealth(result);
      setStatus((current) => ({ ...current, error: '' }));
      return result;
    } catch (error) {
      setHealth(null);
      setStatus((current) => ({ ...current, error: error.message }));
      throw error;
    }
  }, []);

  const refreshDocuments = useCallback(async () => {
    if (!profile.userId) return [];
    try {
      const result = await listDocuments(profile.userId);
      const docs = result.documents || [];
      setDocuments(docs);
      return docs;
    } catch {
      setDocuments([]);
      return [];
    }
  }, [profile.userId]);

  const useCurrentLocation = useCallback(() => new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not available in this browser'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const coords = {
          latitude: Number(position.coords.latitude.toFixed(6)),
          longitude: Number(position.coords.longitude.toFixed(6)),
        };
        updateProfile(coords);
        resolve(coords);
      },
      () => reject(new Error('Location permission was denied')),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 300000 },
    );
  }), [updateProfile]);

  const saveResult = useCallback((result) => {
    const enriched = { ...result, received_at: new Date().toISOString() };
    setLatestResult(enriched);
    localStorage.setItem('kisansetu_latest_result', JSON.stringify(enriched));
    return enriched;
  }, []);

  const runTextQuery = useCallback(async (text) => {
    setStatus({ loading: true, error: '', message: 'Processing request' });
    try {
      const result = await sendTextQuery({
        userId: profile.userId,
        text,
        latitude: profile.latitude || 0,
        longitude: profile.longitude || 0,
        deviceLanguage: lang,
      });
      const saved = saveResult(result);
      await refreshDocuments();
      setStatus({ loading: false, error: '', message: 'Request completed' });
      return saved;
    } catch (error) {
      setStatus({ loading: false, error: error.message, message: '' });
      throw error;
    }
  }, [lang, profile.latitude, profile.longitude, profile.userId, refreshDocuments, saveResult]);

  const runVoiceQuery = useCallback(async (audioBlob, context = null) => {
    setStatus({ loading: true, error: '', message: 'Uploading voice request' });
    try {
      const result = await sendVoiceSync({
        userId: profile.userId,
        audioBlob,
        latitude: profile.latitude || 0,
        longitude: profile.longitude || 0,
        deviceLanguage: lang,
        context,
      });
      const saved = saveResult(result);
      await refreshDocuments();
      setStatus({ loading: false, error: '', message: 'Voice request completed' });
      return saved;
    } catch (error) {
      const queueItem = {
        id: crypto.randomUUID(),
        type: 'voice',
        created_at: new Date().toISOString(),
        reason: error.message,
      };
      setPendingQueue((current) => {
        const next = [queueItem, ...current];
        localStorage.setItem('kisansetu_pending_queue', JSON.stringify(next));
        return next;
      });
      setStatus({ loading: false, error: error.message, message: 'Voice request saved locally' });
      throw error;
    }
  }, [lang, profile.latitude, profile.longitude, profile.userId, refreshDocuments, saveResult]);

  const addToQueue = useCallback((item) => {
    const queueItem = {
      id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      ...item,
    };
    setPendingQueue((current) => {
      const next = [queueItem, ...current];
      localStorage.setItem('kisansetu_pending_queue', JSON.stringify(next));
      return next;
    });
    setStatus((current) => ({ ...current, message: 'Saved locally for later sync' }));
    return queueItem;
  }, []);

  const clearLocalData = useCallback(() => {
    localStorage.removeItem('kisansetu_latest_result');
    localStorage.removeItem('kisansetu_pending_queue');
    setLatestResult(null);
    setPendingQueue([]);
    setStatus({ loading: false, error: '', message: 'Local data cleared' });
  }, []);

  const value = useMemo(() => ({
    apiBase,
    updateApiBase,
    profile,
    updateProfile,
    health,
    refreshHealth,
    documents,
    refreshDocuments,
    latestResult,
    pendingQueue,
    status,
    runTextQuery,
    runVoiceQuery,
    useCurrentLocation,
    addToQueue,
    clearLocalData,
    documentUrl,
  }), [apiBase, updateApiBase, profile, updateProfile, health, refreshHealth, documents, refreshDocuments, latestResult, pendingQueue, status, runTextQuery, runVoiceQuery, useCurrentLocation, addToQueue, clearLocalData]);

  // Clear cached result when language changes so next query uses the new language
  const prevLangRef = useRef(lang);
  useEffect(() => {
    if (prevLangRef.current !== lang) {
      prevLangRef.current = lang;
      setLatestResult(null);
      localStorage.removeItem('kisansetu_latest_result');
    }
  }, [lang]);

  useEffect(() => {
    refreshHealth().catch(() => {});
  }, [apiBase, refreshHealth]);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  return (
    <AppDataContext.Provider value={value}>
      {children}
    </AppDataContext.Provider>
  );
}

export function useAppData() {
  return useContext(AppDataContext);
}
