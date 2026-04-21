/**
 * Next.js Middleware for Supabase Auth
 * COPY THIS FILE to your project root (same level as app/)
 * 
 * Handles:
 * - Session refresh on each request
 * - Protected route redirection
 * - Public route allowlist
 */

import { NextResponse, type NextRequest } from 'next/server';
import { createServerClient } from '@supabase/ssr';

// ============================================================================
// CUSTOMIZE THESE FOR YOUR APP
// ============================================================================

/** Routes that don't require authentication */
const PUBLIC_ROUTES = [
  '/',
  '/auth/login',
  '/auth/signup',
  '/auth/forgot-password',
  '/auth/reset-password',
  '/auth/callback',
  '/auth/verify',
];

/** Route prefixes that don't require authentication */
const PUBLIC_PREFIXES = [
  '/api/public/',
  '/_next/',
  '/favicon.ico',
];

/** Where to redirect unauthenticated users */
const LOGIN_ROUTE = '/auth/login';

/** Where to redirect authenticated users trying to access auth pages */
const DASHBOARD_ROUTE = '/dashboard';

// ============================================================================
// MIDDLEWARE LOGIC (generally don't need to modify)
// ============================================================================

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Skip public prefixes (static files, API routes, etc.)
  if (PUBLIC_PREFIXES.some(prefix => pathname.startsWith(prefix))) {
    return NextResponse.next();
  }

  // Create response to modify
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  });

  // Create Supabase client with cookie handling
  const supabase = createServerClient(
    process.env['NEXT_PUBLIC_SUPABASE_URL']!,
    process.env['NEXT_PUBLIC_SUPABASE_ANON_KEY']!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          // Update request cookies
          cookiesToSet.forEach(({ name, value }) => {
            request.cookies.set(name, value);
          });
          // Create new response with updated cookies
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          });
          // Set cookies on response
          cookiesToSet.forEach(({ name, value, options }) => {
            response.cookies.set(name, value, options);
          });
        },
      },
    }
  );

  // Refresh session (important for token refresh)
  const { data: { user } } = await supabase.auth.getUser();

  const isPublicRoute = PUBLIC_ROUTES.includes(pathname);
  const isAuthRoute = pathname.startsWith('/auth/');

  // Unauthenticated user trying to access protected route
  if (!user && !isPublicRoute) {
    const redirectUrl = new URL(LOGIN_ROUTE, request.url);
    redirectUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(redirectUrl);
  }

  // Authenticated user trying to access login/signup
  if (user && isAuthRoute && !pathname.includes('callback')) {
    return NextResponse.redirect(new URL(DASHBOARD_ROUTE, request.url));
  }

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
