import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { api, type AuthUser } from '../lib/api';

type AuthContextType = {
  token: string | null;
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, preferredLanguage?: string) => Promise<void>;
  updateProfile: (payload: Partial<AuthUser> & { preferred_language?: string; consent_given?: boolean }) => Promise<AuthUser>;
  logout: () => void;
  setSession: (token: string, user: AuthUser) => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'nyaya_setu_token';
const USER_KEY = 'nyaya_setu_user';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  }, [user]);

  const setSession = (nextToken: string, nextUser: AuthUser) => {
    setToken(nextToken);
    setUser(nextUser);
  };

  const refreshUserProfile = async (nextToken: string) => {
    const profile = await api.getProfile(nextToken);
    setUser(profile);
    return profile;
  };

  const updateProfile = async (payload: Partial<AuthUser> & { preferred_language?: string; consent_given?: boolean }) => {
    if (!token) {
      throw new Error('No active session.');
    }
    const profile = await api.updateProfile(token, payload);
    setUser(profile);
    return profile;
  };

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const result = await api.login({ email, password });
      const profile = await refreshUserProfile(result.access_token);
      setSession(result.access_token, profile);
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email: string, password: string, preferredLanguage = 'en') => {
    setLoading(true);
    try {
      await api.register({ email, password, preferred_language: preferredLanguage, consent_given: true });
      const result = await api.login({ email, password });
      const profile = await refreshUserProfile(result.access_token);
      setSession(result.access_token, profile);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const value: AuthContextType = { token, user, loading, login, signup, updateProfile, logout, setSession };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
