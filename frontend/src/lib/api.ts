export type AuthUser = {
  id: number;
  email: string;
  role: string;
  preferred_language: string;
  consent_given: boolean;
  full_name?: string | null;
  phone?: string | null;
  city?: string | null;
  issue_type?: string | null;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type ChatReply = {
  your_right?: string;
  what_law_says?: string | string[];
  what_this_means?: string;
  what_you_can_do?: string | string[];
  remedy?: string;
  next_step?: string;
  citations?: Array<string | Record<string, unknown>>;
  source?: string | Record<string, unknown> | null;
  disclaimer?: string;
  fallback_used?: boolean;
  service_error?: boolean;
  // Drafting fields
  draft_text?: string;
  pdf_path?: string;
  docx_path?: string;
  // Document analysis fields
  user_document_extraction?: Record<string, unknown>;
  ai_interpretation?: string;
  // Lawyer matching fields
  matches?: Array<Record<string, unknown>>;
  // Research fields
  provisions?: string[];
  summary?: string;
  // Catch-all for unknown fields
  [key: string]: unknown;
};

export type ChatAPIResponse = {
  conversation_id: string;
  reply: ChatReply;
  next_action?: string | null;
  evidence_status?: string | null;
};

export type VoiceResponse = {
  conversation_id: string;
  transcript: string;
  reply_text: string;
  reply_audio_b64?: string | null;
  next_action?: string | null;
  service_error?: boolean;
};

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) || 'http://127.0.0.1:8000/api/v1';

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const payload = await response.text();
  const data = payload ? JSON.parse(payload) : null;

  if (!response.ok) {
    const message = typeof data?.detail === 'string' ? data.detail : 'Request failed';
    throw new Error(message);
  }

  return data as T;
}

export const api = {
  async health() {
    return request<{ status: string; version: string; database: string; qdrant: string }>(`/health`);
  },

  async register({ email, password, preferred_language = 'en', consent_given = true }: {
    email: string;
    password: string;
    preferred_language?: string;
    consent_given?: boolean;
  }) {
    return request<AuthUser>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, preferred_language, consent_given }),
    });
  },

  async login({ email, password }: { email: string; password: string }) {
    return request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  async getProfile(token: string) {
    return request<AuthUser>('/users/me', { method: 'GET' }, token);
  },

  async updateProfile(token: string, payload: Partial<AuthUser> & { preferred_language?: string; consent_given?: boolean }) {
    return request<AuthUser>('/users/me', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }, token);
  },

  async uploadDocument(token: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return request<{ id: number; original_filename: string; doc_type?: string | null; storage_ref: string }>(
      '/documents/upload',
      {
        method: 'POST',
        body: formData,
      },
      token,
    );
  },

  async askQuestion(token: string, message: string, conversationId?: string | null) {
    return request<{ conversation_id: string; reply: ChatReply; next_action?: string; evidence_status?: string }>(
      '/chat/message',
      {
        method: 'POST',
        body: JSON.stringify({ message, conversation_id: conversationId ?? null }),
      },
      token,
    );
  },

  async voiceChat(token: string, audioBlob: Blob, conversationId?: string | null) {
    const formData = new FormData();
    formData.append('file', audioBlob, 'voice.webm');
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }

    return request<VoiceResponse>(
      '/voice/chat',
      {
        method: 'POST',
        body: formData,
      },
      token,
    );
  },

  async transcribeAudio(token: string, blob: Blob, language: string): Promise<{ text: string; language: string }> {
    const formData = new FormData();
    formData.append('file', blob, 'voice.webm');
    formData.append('language', language);

    return request<{ text: string; language: string }>(
      '/speech/transcribe',
      {
        method: 'POST',
        body: formData,
      },
      token,
    );
  },

  async synthesizeText(token: string, text: string, language: string): Promise<Blob> {
    const response = await fetch(`${API_BASE}/speech/synthesize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ text, language }),
    });
    if (!response.ok) {
      const payload = await response.text();
      let msg = 'Request failed';
      try {
        const data = JSON.parse(payload);
        msg = data?.detail || msg;
      } catch {}
      throw new Error(msg);
    }
    return response.blob();
  },
};
