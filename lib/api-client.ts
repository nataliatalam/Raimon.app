'use client';

import { z } from 'zod';
import { clearSession, getStoredSession, saveSession } from './session';
import type { ApiErrorResponse, ApiSuccessResponse, AuthSuccessPayload } from '../types/api';

/**
 * Supports BOTH:
 * - NEXT_PUBLIC_API_BASE_URL="/api"  (Next rewrites/proxy)
 * - NEXT_PUBLIC_API_BASE_URL="http://localhost:8000" (direct FastAPI)
 *
 * And avoids accidental "/api/api/..." double prefix.
 */
const RAW_API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
const API_BASE = RAW_API_BASE.replace(/\/+$/, ''); // trim trailing slashes

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

type ApiFetchOptions = {
  method?: string;
  body?: BodyInit | Record<string, unknown> | null;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  skipAuth?: boolean;
};

let refreshPromise: Promise<string | null> | null = null;

function resolveUrl(path: string): string {
  // absolute url passed in
  if (path.startsWith('http://') || path.startsWith('https://')) return path;

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;

  // If API_BASE is a relative prefix like "/api", allow callers to pass either:
  // - "/api/..." (already prefixed)
  // - "/users/..." (we prefix it)
  if (API_BASE.startsWith('/')) {
    if (normalizedPath.startsWith(API_BASE + '/') || normalizedPath === API_BASE) {
      return normalizedPath;
    }
    return `${API_BASE}${normalizedPath}`;
  }

  // API_BASE is absolute origin like "http://localhost:8000"
  return `${API_BASE}${normalizedPath}`;
}

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  const { refreshToken } = getStoredSession();
  if (!refreshToken) return null;

  refreshPromise = (async () => {
    try {
      const response = await fetch(resolveUrl('/api/auth/refresh-token'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        clearSession();
        return null;
      }

      const data = (await response.json()) as ApiSuccessResponse<AuthSuccessPayload>;
      if (!data.success) {
        clearSession();
        return null;
      }

      saveSession({
        accessToken: data.data.token,
        refreshToken: data.data.refresh_token,
      });

      return data.data.token;
    } catch {
      clearSession();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

function buildHeaders(baseHeaders?: Record<string, string>, includeJson = true) {
  const headers = new Headers(baseHeaders);
  if (includeJson && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  return headers;
}

async function parseError(response: Response) {
  let payload: ApiErrorResponse | null = null;
  try {
    payload = (await response.json()) as ApiErrorResponse;
  } catch {
    // ignore
  }

  const message =
    payload?.message ??
    payload?.error?.message ??
    `Request failed with status ${response.status}`;

  throw new ApiError(message, response.status, payload);
}

export async function apiFetch<TResponse>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<TResponse> {
  const { method = 'GET', headers: customHeaders, body, signal, skipAuth } = options;
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

  const url = resolveUrl(path);

  const headers = buildHeaders(customHeaders, !isFormData);

  const accessToken = getStoredSession().accessToken;
  if (accessToken && !skipAuth) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const fetchOptions: RequestInit = {
    method,
    headers,
    signal,
    body: isFormData ? (body as BodyInit) : body ? JSON.stringify(body) : undefined,
  };

  let response = await fetch(url, fetchOptions);

  // Auto-refresh on 401 (unless skipAuth)
  if (response.status === 401 && !skipAuth) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers.set('Authorization', `Bearer ${newToken}`);
      response = await fetch(url, { ...fetchOptions, headers });
    }
  }

  if (!response.ok) {
    await parseError(response);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  const data = (await response.json()) as TResponse;
  return data;
}

export class ValidationError extends Error {
  issues: z.ZodIssue[];

  constructor(issues: z.ZodIssue[]) {
    super(`Response validation failed: ${issues.map((i) => i.message).join(', ')}`);
    this.name = 'ValidationError';
    this.issues = issues;
  }
}

export async function apiFetchValidated<T>(
  path: string,
  schema: z.ZodType<T>,
  options: ApiFetchOptions = {},
): Promise<T> {
  const data = await apiFetch<unknown>(path, options);

  const result = schema.safeParse(data);
  if (!result.success) {
    console.error('API Response Validation Error:', result.error.issues);
    throw new ValidationError(result.error.issues);
  }

  return result.data;
}
