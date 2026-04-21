/**
 * Auth Type Definitions
 * CUSTOMIZE: Edit UserRole and UserProfile to match your app's needs
 */

import type { User, Session } from '@supabase/supabase-js';

// ============================================================================
// CUSTOMIZE THESE FOR YOUR APP
// ============================================================================

/**
 * User roles for your application
 * ADD/REMOVE roles as needed for your app
 */
export const UserRole = [
  'admin',
  'user',
  'staff',
  // Add your roles here, e.g.:
  // 'manager',
  // 'billing',
  // 'provider',
] as const;

export type UserRole = (typeof UserRole)[number];

/**
 * User profile shape (matches your profiles/users table)
 * MODIFY to match your database schema
 */
export interface UserProfile {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  role: UserRole;
  created_at: string;
  // Add your custom fields here, e.g.:
  // avatar_url?: string;
  // phone?: string;
  // organization_id?: string;
}

// ============================================================================
// DO NOT MODIFY BELOW (unless you know what you're doing)
// ============================================================================

/**
 * Auth context state
 */
export interface AuthState {
  user: User | null;
  session: Session | null;
  profile: UserProfile | null;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Auth context value (state + methods)
 */
export interface AuthContextValue extends AuthState {
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signUp: (email: string, password: string, metadata?: Record<string, unknown>) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  sendOTP: (email: string) => Promise<{ error: Error | null }>;
  verifyOTP: (email: string, token: string) => Promise<{ error: Error | null }>;
  updatePassword: (password: string) => Promise<{ error: Error | null }>;
  refreshSession: () => Promise<void>;
}

/**
 * Sign in form data
 */
export interface SignInFormData {
  email: string;
  password: string;
  remember?: boolean;
}

/**
 * Sign up form data
 */
export interface SignUpFormData {
  email: string;
  password: string;
  confirmPassword: string;
  firstName?: string;
  lastName?: string;
}
