/**
 * AuthProvider Component
 * Wraps your app to provide authentication context
 * 
 * @example
 * // app/layout.tsx
 * import { AuthProvider } from '@/auth-template/components/AuthProvider';
 * 
 * export default function RootLayout({ children }) {
 *   return (
 *     <html>
 *       <body>
 *         <AuthProvider>{children}</AuthProvider>
 *       </body>
 *     </html>
 *   );
 * }
 */

'use client';

import { createContext, useCallback, useEffect, useState } from 'react';
import { createClient } from '../lib/supabase/client';
import type { User, Session } from '@supabase/supabase-js';
import type { AuthContextValue, UserProfile } from '../types/auth';

// Create context with undefined default (will throw if used outside provider)
export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
  /** Table name for user profiles (default: 'profiles') */
  profilesTable?: string;
}

export function AuthProvider({ 
  children, 
  profilesTable = 'profiles' 
}: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  const supabase = createClient();

  // Fetch user profile from database
  const fetchProfile = useCallback(async (userId: string) => {
    try {
      const { data, error: profileError } = await supabase
        .from(profilesTable)
        .select('*')
        .eq('id', userId)
        .single();
      
      if (profileError) {
        console.error('Error fetching profile:', profileError);
        setProfile(null);
        return;
      }
      
      setProfile(data as UserProfile);
    } catch (err) {
      console.error('Error fetching profile:', err);
      setProfile(null);
    }
  }, [supabase, profilesTable]);

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      try {
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        
        setSession(currentSession);
        setUser(currentSession?.user ?? null);
        
        if (currentSession?.user) {
          await fetchProfile(currentSession.user.id);
        }
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, newSession) => {
        setSession(newSession);
        setUser(newSession?.user ?? null);
        
        if (newSession?.user) {
          await fetchProfile(newSession.user.id);
        } else {
          setProfile(null);
        }
        
        setIsLoading(false);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase, fetchProfile]);

  // Auth methods
  const signIn = useCallback(async (email: string, password: string) => {
    try {
      setError(null);
      const { error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      if (signInError) {
        setError(signInError);
        return { error: signInError };
      }
      
      return { error: null };
    } catch (err) {
      const error = err as Error;
      setError(error);
      return { error };
    }
  }, [supabase]);

  const signUp = useCallback(async (
    email: string, 
    password: string,
    metadata?: Record<string, unknown>
  ) => {
    try {
      setError(null);
      const { error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: metadata,
        },
      });
      
      if (signUpError) {
        setError(signUpError);
        return { error: signUpError };
      }
      
      return { error: null };
    } catch (err) {
      const error = err as Error;
      setError(error);
      return { error };
    }
  }, [supabase]);

  const signOut = useCallback(async () => {
    try {
      setError(null);
      await supabase.auth.signOut();
      setUser(null);
      setSession(null);
      setProfile(null);
    } catch (err) {
      setError(err as Error);
    }
  }, [supabase]);

  const sendOTP = useCallback(async (email: string) => {
    try {
      setError(null);
      const { error: otpError } = await supabase.auth.signInWithOtp({
        email,
        options: { shouldCreateUser: true },
      });
      if (otpError) {
        setError(otpError);
        return { error: otpError };
      }
      return { error: null };
    } catch (err) {
      const error = err as Error;
      setError(error);
      return { error };
    }
  }, [supabase]);

  const verifyOTP = useCallback(async (email: string, token: string) => {
    try {
      setError(null);
      const { error: verifyError } = await supabase.auth.verifyOtp({
        email,
        token,
        type: 'email',
      });
      if (verifyError) {
        setError(verifyError);
        return { error: verifyError };
      }
      return { error: null };
    } catch (err) {
      const error = err as Error;
      setError(error);
      return { error };
    }
  }, [supabase]);


  const updatePassword = useCallback(async (password: string) => {
    try {
      setError(null);
      const { error: updateError } = await supabase.auth.updateUser({
        password,
      });
      
      if (updateError) {
        setError(updateError);
        return { error: updateError };
      }
      
      return { error: null };
    } catch (err) {
      const error = err as Error;
      setError(error);
      return { error };
    }
  }, [supabase]);

  const refreshSession = useCallback(async () => {
    try {
      const { data: { session: refreshedSession } } = await supabase.auth.refreshSession();
      setSession(refreshedSession);
      setUser(refreshedSession?.user ?? null);
    } catch (err) {
      setError(err as Error);
    }
  }, [supabase]);

  const value: AuthContextValue = {
    user,
    session,
    profile,
    isLoading,
    error,
    signIn,
    signUp,
    signOut,
    sendOTP,
    verifyOTP,
    updatePassword,
    refreshSession,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
