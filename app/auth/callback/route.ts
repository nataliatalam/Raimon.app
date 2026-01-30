import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get('code');
  const next = searchParams.get('next') ?? '/onboarding-questions';

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    return NextResponse.redirect(`${origin}/login?error=config`);
  }

  if (code) {
    const cookieStore = await cookies();

    // Track cookies that need to be set on the response
    const cookiesToSetOnResponse: { name: string; value: string; options?: any }[] = [];

    const supabase = createServerClient(supabaseUrl, supabaseKey,
      {
        cookies: {
          getAll() {
            return cookieStore.getAll();
          },
          setAll(cookiesToSet) {
            cookiesToSet.forEach(({ name, value, options }) => {
              // Store for setting on redirect response
              cookiesToSetOnResponse.push({ name, value, options });
              try {
                cookieStore.set(name, value, options);
              } catch {
                // Ignore errors from Server Component
              }
            });
          },
        },
      }
    );

    const { data, error } = await supabase.auth.exchangeCodeForSession(code);

    console.log('OAuth callback: code exchange result', {
      hasSession: !!data?.session,
      error: error?.message,
      accessTokenLength: data?.session?.access_token?.length
    });

    if (!error && data.session) {
      // Redirect to a client page that will handle the backend JWT exchange
      const forwardUrl = new URL('/auth/complete', origin);
      forwardUrl.searchParams.set('next', next);

      const response = NextResponse.redirect(forwardUrl);

      // Set all auth cookies on the redirect response
      cookiesToSetOnResponse.forEach(({ name, value, options }) => {
        response.cookies.set(name, value, options);
      });

      return response;
    }

    console.error('OAuth callback failed:', error?.message);
  }

  // Return to login with error
  return NextResponse.redirect(`${origin}/login?error=oauth_failed`);
}
