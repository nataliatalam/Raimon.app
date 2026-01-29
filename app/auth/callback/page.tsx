'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  { auth: { detectSessionInUrl: true, flowType: 'pkce' } }
);

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    (async () => {
      // exchange PKCE code -> session
      const { error } = await supabase.auth.exchangeCodeForSession(window.location.href);
      if (error) {
        router.replace('/login?error=oauth');
        return;
      }

      // decide where to go
      const { data } = await supabase.auth.getUser();
      const u: any = data.user;

      const onboardingCompleted =
        !!u?.onboarding_completed || !!u?.user_metadata?.onboarding_completed;

      router.replace(onboardingCompleted ? '/dashboard' : '/onboarding-questions');
    })();
  }, [router]);

  return <div style={{ padding: 24, opacity: 0.8 }}>Signing you in…</div>;
}
