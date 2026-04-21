# Auth Template for Next.js + Supabase

Drop-in authentication for any Next.js 14+ App Router project using Supabase.

## Quick Start

1. Copy this entire folder to your project root
2. Run: `npm install @supabase/ssr @supabase/supabase-js`
3. Add env vars to `.env.local`:
   ```
   NEXT_PUBLIC_SUPABASE_URL=your-project-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-key
   ```
4. Copy `middleware.ts` to your project root
5. Import components as needed

## File Structure

```
auth-template/
├── README.md              # This file
├── CURSOR_RULES.md        # CRITICAL: Cursor must read this
├── .cursorrules           # Auto-loaded by Cursor
├── middleware.ts          # Copy to project root
├── lib/
│   └── supabase/
│       ├── client.ts      # Browser client
│       ├── server.ts      # Server client  
│       └── admin.ts       # Service role client
├── components/
│   ├── AuthProvider.tsx   # Wrap app with this
│   ├── SignIn.tsx         # Email/password login
│   ├── SignUp.tsx         # Registration
│   ├── SignOut.tsx        # Logout button
│   ├── MagicLink.tsx      # Passwordless login
│   ├── ResetPassword.tsx  # Password reset flow
│   └── ProtectedRoute.tsx # Client-side guard
├── hooks/
│   ├── useAuth.ts         # Auth state hook
│   ├── useSession.ts      # Session data hook
│   └── useRequireAuth.ts  # Redirect if not authed
├── types/
│   └── auth.ts            # Auth type definitions
└── utils/
    └── roles.ts           # Role helpers
```

## Usage

### Wrap your app
```tsx
// app/layout.tsx
import { AuthProvider } from '@/auth-template/components/AuthProvider';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
```

### Use auth hook
```tsx
'use client';
import { useAuth } from '@/auth-template/hooks/useAuth';

export default function Dashboard() {
  const { user, profile, isLoading, signOut } = useAuth();
  
  if (isLoading) return <div>Loading...</div>;
  if (!user) return <div>Not authenticated</div>;
  
  return <div>Welcome {profile?.first_name}</div>;
}
```

### Add login page
```tsx
// app/auth/login/page.tsx
import { SignIn } from '@/auth-template/components/SignIn';

export default function LoginPage() {
  return <SignIn redirectTo="/dashboard" />;
}
```
