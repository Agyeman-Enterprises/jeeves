# CURSOR_RULES.md - READ THIS BEFORE MODIFYING AUTH

## ⛔ STOP - READ THIS FIRST

This project uses a **standardized auth template**. DO NOT:
- Create new Supabase client files
- Implement custom JWT handling
- Use NextAuth, Firebase, Auth0, or Clerk
- Store tokens in React state
- Create alternative auth hooks

## ✅ ALWAYS USE THESE FILES

| Need | Use This File |
|------|---------------|
| Browser Supabase client | `auth-template/lib/supabase/client.ts` |
| Server Supabase client | `auth-template/lib/supabase/server.ts` |
| Admin/service client | `auth-template/lib/supabase/admin.ts` |
| Auth state in components | `useAuth()` from `auth-template/hooks/useAuth` |
| Protect a page | `useRequireAuth()` from `auth-template/hooks/useRequireAuth` |
| Login form | `<SignIn />` from `auth-template/components/SignIn` |
| Logout button | `<SignOut />` from `auth-template/components/SignOut` |
| Role checking | `hasRole()` from `auth-template/utils/roles` |
| Route protection | `middleware.ts` in project root |

## 📋 CODE PATTERNS

### Server-Side (API Routes, Server Components)

```typescript
import { createClient } from '@/auth-template/lib/supabase/server';

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }
  
  // Fetch profile for role check
  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single();
    
  // Now use profile.role for authorization
}
```

### Client-Side (React Components)

```typescript
'use client';
import { useAuth } from '@/auth-template/hooks/useAuth';

export function MyComponent() {
  const { user, profile, isLoading, signOut } = useAuth();
  
  if (isLoading) return <div>Loading...</div>;
  if (!user) return <div>Please sign in</div>;
  
  return <div>Hello {profile?.first_name}</div>;
}
```

### Protected Page

```typescript
'use client';
import { useRequireAuth } from '@/auth-template/hooks/useRequireAuth';

export default function AdminPage() {
  // Redirects to login if not authenticated
  // Redirects to /auth/unauthorized if wrong role
  const { user, profile } = useRequireAuth({ 
    requiredRole: 'admin' 
  });
  
  return <div>Admin content</div>;
}
```

### Role Checking

```typescript
import { hasRole, hasAnyRole, normalizeRole } from '@/auth-template/utils/roles';

// Check specific role
if (hasRole(profile.role, 'admin')) { ... }

// Check any of multiple roles
if (hasAnyRole(profile.role, ['admin', 'staff'])) { ... }

// Normalize legacy role names
const role = normalizeRole('administrator'); // Returns 'admin'
```

## 🚫 FORBIDDEN PATTERNS

```typescript
// ❌ NEVER create new Supabase clients
import { createClient } from '@supabase/supabase-js';
const supabase = createClient(url, key); // WRONG

// ❌ NEVER store tokens in state
const [token, setToken] = useState(session.access_token); // WRONG

// ❌ NEVER implement custom JWT
import jwt from 'jsonwebtoken';
jwt.sign(payload, secret); // WRONG

// ❌ NEVER expose detailed auth errors
setError(error.message); // WRONG - reveals user existence

// ❌ NEVER skip profile fetch after auth
if (user) { /* use user directly */ } // WRONG - need profile for role

// ❌ NEVER hardcode role strings
if (role === 'admin') // WRONG - use hasRole()
```

## 🔧 CUSTOMIZATION POINTS

When adapting for a new project, ONLY modify:

1. **`auth-template/types/auth.ts`**
   - `UserRole` array - add/remove roles
   - `UserProfile` interface - match your DB schema

2. **`auth-template/utils/roles.ts`**
   - `ROLE_HIERARCHY` - define permission levels
   - `ROLE_DISPLAY_NAMES` - human-readable names
   - `ROLE_HOME_PATHS` - post-login redirects
   - `LEGACY_MAPPINGS` - handle old role names

3. **`middleware.ts`** (in project root)
   - `PUBLIC_ROUTES` - pages that don't need auth
   - `PUBLIC_PREFIXES` - API routes that don't need auth

4. **`AuthProvider` props**
   - `profilesTable` - if your profiles table has different name

## 📁 FILE STRUCTURE

```
your-project/
├── middleware.ts              # COPY from auth-template/middleware.ts
├── auth-template/             # COPY entire folder
│   ├── index.ts               # Main exports
│   ├── .cursorrules           # Auto-loaded constraints
│   ├── CURSOR_RULES.md        # This file
│   ├── lib/supabase/
│   │   ├── client.ts          # Browser client
│   │   ├── server.ts          # Server client
│   │   └── admin.ts           # Service role client
│   ├── components/
│   │   ├── AuthProvider.tsx   # Context provider
│   │   ├── SignIn.tsx         # Login form
│   │   ├── SignUp.tsx         # Registration
│   │   └── SignOut.tsx        # Logout button
│   ├── hooks/
│   │   ├── useAuth.ts         # Main auth hook
│   │   ├── useSession.ts      # Session only
│   │   └── useRequireAuth.ts  # Protected route hook
│   ├── types/
│   │   └── auth.ts            # Type definitions
│   └── utils/
│       └── roles.ts           # Role helpers
└── .env.local
    ├── NEXT_PUBLIC_SUPABASE_URL=
    ├── NEXT_PUBLIC_SUPABASE_ANON_KEY=
    └── SUPABASE_SERVICE_ROLE_KEY=
```

## 🧪 TESTING CHECKLIST

Before considering auth complete:

- [ ] User can sign up and receives verification email
- [ ] User can sign in with email/password
- [ ] Session persists on page refresh
- [ ] User can sign out
- [ ] Protected routes redirect to login when not authenticated
- [ ] Authenticated users are redirected from /auth/login to dashboard
- [ ] Role-based access works (admin can access admin routes, etc.)
- [ ] Password reset flow works
- [ ] No auth tokens visible in browser devtools Application tab (only httpOnly cookies)

## 💬 WHEN CURSOR VIOLATES THESE RULES

Copy this into chat:

> "STOP. Read CURSOR_RULES.md in auth-template folder. You violated: [specific rule]. 
> Use existing auth-template files. Do not create new auth implementations."
