/**
 * useSession Hook
 * Lightweight hook for just session data (no methods)
 * 
 * @example
 * const { session, isLoading } = useSession();
 */

'use client';

import { useAuth } from './useAuth';

export function useSession() {
  const { session, isLoading } = useAuth();
  
  return {
    session,
    isLoading,
    isAuthenticated: !!session,
  };
}
