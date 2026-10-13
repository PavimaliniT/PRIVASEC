import { create } from 'zustand';
import { api } from './api';

export interface User {
  id: string;
  email: string;
  role: string;
  pseudonym?: string;
  mfa_enabled: boolean;
  organization_id: string;
  organization_name?: string;
}

interface AuthState {
  user: User | null;
  session: any | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setSession: (session: any | null) => void;
  checkAuth: () => Promise<boolean>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  session: null,
  isLoading: true,
  isAuthenticated: false,

  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setSession: (session) => set({ session }),

  checkAuth: async () => {
    try {
      set({ isLoading: true });
      const data = await api.auth.me();
      if (data && data.id) {
        set({
          user: {
            id: data.id,
            email: data.email,
            role: data.role,
            pseudonym: data.pseudonym,
            mfa_enabled: data.mfa_enabled,
            organization_id: data.organization_id,
          },
          session: data.session,
          isAuthenticated: true,
          isLoading: false,
        });
        return true;
      }
    } catch {
      // Not logged in or expired
    }
    set({ user: null, session: null, isAuthenticated: false, isLoading: false });
    return false;
  },

  logout: async () => {
    try {
      await api.auth.logout();
    } catch {
      // Ignore
    }
    localStorage.removeItem('privasec_token');
    set({ user: null, session: null, isAuthenticated: false });
  },
}));
