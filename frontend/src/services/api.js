/**
 * API service - Simple fetch wrappers for backend endpoints.
 * All endpoints expect base URL: http://localhost:8000
 */

const BASE_URL = 'http://localhost:8000';

/**
 * Send handwriting image as FormData. Returns { risk_score }.
 */
export async function predictHandwriting(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE_URL}/predict/handwriting`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Handwriting prediction failed');
  return res.json();
}

/**
 * Send speech audio as FormData. Returns { risk_score }.
 */
export async function predictSpeech(audioBlob) {
  const formData = new FormData();
  formData.append('file', audioBlob);
  const res = await fetch(`${BASE_URL}/predict/speech`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Speech prediction failed');
  return res.json();
}

/**
 * Send cognitive metrics as JSON. Returns { risk_score }.
 */
export async function predictCognitive(metrics) {
  const res = await fetch(`${BASE_URL}/predict/cognitive`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metrics),
  });
  if (!res.ok) throw new Error('Cognitive prediction failed');
  return res.json();
}

/**
 * Send all scores for final result. Returns { final_risk, explanations }.
 */
export async function predictFinal(scores) {
  const res = await fetch(`${BASE_URL}/predict/final`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(scores),
  });
  if (!res.ok) throw new Error('Final prediction failed');
  return res.json();
}
