const DEFAULT_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function getApiBase() {
  return localStorage.getItem('kisansetu_api_base') || DEFAULT_API_BASE;
}

export function setApiBase(value) {
  localStorage.setItem('kisansetu_api_base', value.replace(/\/$/, ''));
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = typeof body === 'string' ? body : body?.detail || 'Request failed';
    throw new Error(message);
  }

  return body;
}

export async function getHealth() {
  const response = await fetch(`${getApiBase()}/api/v1/health`);
  return parseResponse(response);
}

export async function sendTextQuery({
  userId,
  text,
  latitude,
  longitude,
  deviceLanguage,
}) {
  const response = await fetch(`${getApiBase()}/api/v1/text/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      text,
      latitude,
      longitude,
      device_language: deviceLanguage,
      idempotency_key: crypto.randomUUID(),
    }),
  });

  return parseResponse(response);
}

export async function sendVoiceSync({
  userId,
  audioBlob,
  latitude,
  longitude,
  deviceLanguage,
  context,
}) {
  const form = new FormData();
  form.append('audio_file', audioBlob, `query-${Date.now()}.webm`);
  form.append('user_id', userId);
  form.append('idempotency_key', crypto.randomUUID());
  form.append('latitude', String(latitude));
  form.append('longitude', String(longitude));
  form.append('device_language', deviceLanguage);
  if (context) form.append('context', context);
  form.append('timestamp', new Date().toISOString());

  const response = await fetch(`${getApiBase()}/api/v1/voice/sync`, {
    method: 'POST',
    body: form,
  });

  return parseResponse(response);
}

export async function listDocuments(userId) {
  const response = await fetch(`${getApiBase()}/api/v1/schemes/documents/${encodeURIComponent(userId)}`);
  return parseResponse(response);
}

export function documentUrl(url) {
  if (!url) return '';
  return url.startsWith('http') ? url : `${getApiBase()}${url}`;
}

export async function sendSchemeChat({
  threadId,
  userId,
  message,
  schemeId,
  schemeData,
  language,
  userState,
  landArea,
}) {
  const response = await fetch(`${getApiBase()}/api/v1/scheme/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      thread_id: threadId || null,
      user_id: userId,
      message,
      scheme_id: schemeId || null,
      scheme_data: schemeData || null,
      language: language || 'hi',
      user_state: userState || null,
      land_area: landArea || 0,
    }),
  });
  return parseResponse(response);
}

export async function getSchemeThreadStatus(threadId) {
  const response = await fetch(`${getApiBase()}/api/v1/scheme/status/${encodeURIComponent(threadId)}`);
  return parseResponse(response);
}

export async function confirmSchemeSubmission({ threadId, approved }) {
  const response = await fetch(`${getApiBase()}/api/v1/scheme/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      thread_id: threadId,
      approved,
    }),
  });
  return parseResponse(response);
}

export async function analyzeCropImage({
  userId,
  imageBase64,
  language,
  latitude,
  longitude,
}) {
  const response = await fetch(`${getApiBase()}/api/v1/crop/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      image_base64: imageBase64,
      language: language || 'hi',
      latitude: latitude || null,
      longitude: longitude || null,
    }),
  });
  return parseResponse(response);
}
