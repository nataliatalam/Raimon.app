'use client';

import type { SessionData, UserProfile } from '../types/api';

const ACCESS_TOKEN_KEY = 'raimon_access_token';
const REFRESH_TOKEN_KEY = 'raimon_refresh_token';
const USER_KEY = 'raimon_user';

type SessionUpdate = {
  accessToken?: string | null;
  refreshToken?: string | null;
  user?: UserProfile | null;
};

const defaultSession: SessionData = {
  accessToken: null,
  refreshToken: null,
  user: null,
};

type Subscriber = (session: SessionData) => void;
const subscribers = new Set<Subscriber>();

function isBrowser() {
  return typeof window !== 'undefined';
}

function readStorage(key: string) {
  if (!isBrowser()) return null;
  return window.localStorage.getItem(key);
}

function writeStorage(key: string, value: string | null) {
  if (!isBrowser()) return;
  if (value === null) {
    window.localStorage.removeItem(key);
  } else {
    window.localStorage.setItem(key, value);
  }
}

export function getStoredSession(): SessionData {
  if (!isBrowser()) {
    return { ...defaultSession };
  }

  const accessToken = readStorage(ACCESS_TOKEN_KEY);
  const refreshToken = readStorage(REFRESH_TOKEN_KEY);
  const rawUser = readStorage(USER_KEY);

  let user: UserProfile | null = null;
  if (rawUser) {
    try {
      user = JSON.parse(rawUser) as UserProfile;
    } catch {
      user = null;
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
  };
}

function notify(session: SessionData) {
  subscribers.forEach((cb) => {
    try {
      cb(session);
    } catch {
      // no-op
    }
  });
}

export function saveSession(update: SessionUpdate) {
  const current = getStoredSession();
  const next: SessionData = {
    accessToken: update.accessToken ?? current.accessToken,
    refreshToken: update.refreshToken ?? current.refreshToken,
    user: update.user ?? current.user,
  };

  writeStorage(ACCESS_TOKEN_KEY, next.accessToken);
  writeStorage(REFRESH_TOKEN_KEY, next.refreshToken);
  writeStorage(USER_KEY, next.user ? JSON.stringify(next.user) : null);

  notify(next);
}

export function clearSession() {
  writeStorage(ACCESS_TOKEN_KEY, null);
  writeStorage(REFRESH_TOKEN_KEY, null);
  writeStorage(USER_KEY, null);
  notify({ ...defaultSession });
}

export function subscribeSession(cb: Subscriber) {
  subscribers.add(cb);
  return () => {
    subscribers.delete(cb);
  };
}

