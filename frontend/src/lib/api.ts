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
  summary?: string;
  [key: string]: unknown;
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
};
