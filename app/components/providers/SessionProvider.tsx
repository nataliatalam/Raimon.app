'use client';

import { createContext, useContext, useCallback, useEffect, useMemo, useState } from 'react';
import type { SessionData, UserProfile } from '../../../types/api';
import { clearSession, getStoredSession, saveSession, subscribeSession } from '../../../lib/session';

type SessionContextValue = {
  session: SessionData;
  status: 'loading' | 'ready';
  setSession: (payload: { accessToken: string; refreshToken: string; user: UserProfile }) => void;
  clear: () => void;
};

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

// Default session to avoid hydration mismatch - localStorage is only read in useEffect
const defaultSession: SessionData = {
  accessToken: null,
  refreshToken: null,
  user: null,
};

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [session, setSessionState] = useState<SessionData>(defaultSession);
  const [status, setStatus] = useState<'loading' | 'ready'>('loading');

  useEffect(() => {
    setSessionState(getStoredSession());
    setStatus('ready');

    const unsubscribe = subscribeSession((next) => {
      setSessionState(next);
      setStatus('ready');
    });

    return unsubscribe;
  }, []);

  const setSession = useCallback(({ accessToken, refreshToken, user }: { accessToken: string; refreshToken: string; user: UserProfile }) => {
    saveSession({ accessToken, refreshToken, user });
  }, []);

  const clear = useCallback(() => {
    clearSession();
  }, []);

  const value = useMemo<SessionContextValue>(
    () => ({
      session,
      status,
      setSession,
      clear,
    }),
    [session, status, setSession, clear],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error('useSession must be used within SessionProvider');
  }
  return ctx;
}

