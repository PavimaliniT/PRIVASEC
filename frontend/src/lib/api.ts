const API_BASE = '/api';

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('privasec_token');
  const headers = new Headers(options.headers || {});

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Only set application/json if not uploading FormData
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // Includes HttpOnly cookies
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail || `HTTP error ${response.status}`);
  }

  // Return blob if response is octet-stream
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/octet-stream')) {
    return (await response.blob()) as unknown as T;
  }

  return response.json();
}

export const api = {
  // Auth
  auth: {
    login: (body: any) => apiRequest('/auth/login', { method: 'POST', body: JSON.stringify(body) }),
    register: (body: any) => apiRequest('/auth/register', { method: 'POST', body: JSON.stringify(body) }),
    me: () => apiRequest('/auth/me'),
    logout: () => apiRequest('/auth/logout', { method: 'POST' }),
    setupMfa: () => apiRequest('/auth/mfa/setup', { method: 'POST' }),
    verifyMfa: (code: string) => apiRequest('/auth/mfa/verify', { method: 'POST', body: JSON.stringify({ totp_code: code }) }),
    stepUp: (code: string) => apiRequest('/auth/step-up', { method: 'POST', body: JSON.stringify({ totp_code: code }) }),
  },

  // Dashboard
  dashboard: {
    overview: () => apiRequest('/dashboard/overview'),
  },

  // Privacy Center
  privacy: {
    scanText: (text: string) => apiRequest('/privacy/scan', { method: 'POST', body: JSON.stringify({ text }) }),
    scanFile: (formData: FormData) => apiRequest('/privacy/scan-file', { method: 'POST', body: formData }),
    mask: (text: string, strategy: string = 'PARTIAL') => apiRequest('/privacy/mask', { method: 'POST', body: JSON.stringify({ text, strategy }) }),
    pseudonymize: (identifier: string, purpose: string = 'analytics') => apiRequest('/privacy/pseudonymize', { method: 'POST', body: JSON.stringify({ identifier, purpose, deterministic: true }) }),
    reidentify: (token: string, justification: string) => apiRequest('/privacy/reidentify', { method: 'POST', body: JSON.stringify({ token, justification }) }),
    diffPrivacyDemo: (epsilon: number, actualCount: number) => apiRequest(`/privacy/diff-privacy-demo?epsilon=${epsilon}&actual_count=${actualCount}`),
    getScans: () => apiRequest('/privacy/scans'),
  },

  // Intelligence & Risk
  intelligence: {
    getAnomalies: () => apiRequest('/anomalies'),
    analyzeAnomaly: (features: any) => apiRequest('/anomalies/analyze', { method: 'POST', body: JSON.stringify(features) }),
    getModelMetrics: () => apiRequest('/anomalies/model-metrics'),
    getBehaviorProfiles: () => apiRequest('/behavior/profiles'),
    getBehaviorProfile: (actor: string) => apiRequest(`/behavior/profiles/${actor}`),
    evaluateRisk: (body: any) => apiRequest('/risk/evaluate', { method: 'POST', body: JSON.stringify(body) }),
    getRiskEvents: () => apiRequest('/risk/events'),
  },

  // Incidents
  incidents: {
    list: (statusFilter?: string, severityFilter?: string) => {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status_filter', statusFilter);
      if (severityFilter) params.append('severity_filter', severityFilter);
      return apiRequest(`/incidents?${params.toString()}`);
    },
    get: (id: string) => apiRequest(`/incidents/${id}`),
    respond: (id: string, actionType: string, reason: string) => apiRequest(`/incidents/${id}/respond`, { method: 'POST', body: JSON.stringify({ action_type: actionType, reason }) }),
    resolve: (id: string, resolutionNote: string, status: string = 'Resolved') => apiRequest(`/incidents/${id}/resolve`, { method: 'POST', body: JSON.stringify({ resolution_note: resolutionNote, status }) }),
    rollback: (actionId: string) => apiRequest(`/incidents/actions/${actionId}/rollback`, { method: 'POST' }),
  },

  // Security Gateway
  security: {
    getEvents: (severity?: string, eventType?: string) => {
      const params = new URLSearchParams();
      if (severity) params.append('severity', severity);
      if (eventType) params.append('event_type', eventType);
      return apiRequest(`/security/events?${params.toString()}`);
    },
    getGatewayStatus: () => apiRequest('/security/gateway-status'),
  },

  // Simulation Lab
  simulation: {
    getScenarios: () => apiRequest('/simulation/scenarios'),
    runScenario: (id: string) => apiRequest(`/simulation/run/${id}`, { method: 'POST' }),
  },

  // Cryptography Lab
  crypto: {
    generateKey: () => apiRequest('/crypto/generate-key'),
    encryptText: (plaintext: string, keyHex?: string) => apiRequest('/crypto/encrypt-text', { method: 'POST', body: JSON.stringify({ plaintext, key_hex: keyHex }) }),
    decryptText: (nonceHex: string, ciphertextHex: string, tagHex: string, keyHex?: string) => apiRequest('/crypto/decrypt-text', { method: 'POST', body: JSON.stringify({ nonce_hex: nonceHex, ciphertext_hex: ciphertextHex, tag_hex: tagHex, key_hex: keyHex }) }),
    hash: (text: string, expectedSha256?: string) => apiRequest('/crypto/hash', { method: 'POST', body: JSON.stringify({ text, expected_sha256: expectedSha256 }) }),
  },

  // Visual Cryptography
  visualCrypto: {
    split: (formData: FormData) => apiRequest('/visual-crypto/split', { method: 'POST', body: formData }),
    reconstruct: (formData: FormData) => apiRequest('/visual-crypto/reconstruct', { method: 'POST', body: formData }),
  },

  // Steganography
  steganography: {
    embed: (formData: FormData) => apiRequest('/steganography/embed', { method: 'POST', body: formData }),
    extract: (formData: FormData) => apiRequest('/steganography/extract', { method: 'POST', body: formData }),
    compare: (formData: FormData) => apiRequest('/steganography/compare', { method: 'POST', body: formData }),
  },

  // Audit
  audit: {
    getLogs: () => apiRequest('/audit/logs'),
    verifyChain: () => apiRequest('/audit/verify'),
  },
};
