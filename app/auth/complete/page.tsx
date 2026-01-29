'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useSession } from '../../components/providers/SessionProvider';
import { apiFetch } from '../../../lib/api-client';
import { createClient } from '../../../lib/supabase/client';
import type { ApiSuccessResponse } from '../../../types/api';

export default function AuthCompletePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setSession } = useSession();
  const supabase = createClient();

  useEffect(() => {
    (async () => {
      try {
        // Get the Supabase session (set by the route handler via cookies)
        const { data: { session } } = await supabase.auth.getSession();

        if (!session) {
          console.error('No Supabase session found');
          window.location.href = '/login?error=no_session';
          return;
        }

        console.log('Auth complete: Got Supabase session, calling backend...');

        // Exchange Supabase token for backend JWT
        const result = await apiFetch<ApiSuccessResponse<{
          user: any;
          token: string;
          refresh_token: string;
        }>>('/api/auth/google', {
          method: 'POST',
          body: { access_token: session.access_token },
          skipAuth: true,
        });

        if (!result.success || !result.data?.token) {
          console.error('Backend JWT exchange failed', result);
          window.location.href = '/login?error=oauth_backend';
          return;
        }

        // Save backend JWT session
        setSession({
          accessToken: result.data.token,
          refreshToken: result.data.refresh_token ?? '',
          user: result.data.user ?? null,
        });

        // Redirect based on onboarding status
        const onboardingCompleted = result.data.user?.onboarding_completed;
        const next = searchParams.get('next') ?? '/onboarding-questions';
        const destination = onboardingCompleted ? '/dashboard' : next;

        console.log('Auth complete: Redirecting to', destination);
        window.location.href = destination;
      } catch (err) {
        console.error('Auth complete error:', err);
        window.location.href = '/login?error=oauth_exception';
      }
    })();
  }, [supabase, setSession, searchParams]);

  return <div style={{ padding: 24, opacity: 0.8 }}>Completing sign in...</div>;
}
