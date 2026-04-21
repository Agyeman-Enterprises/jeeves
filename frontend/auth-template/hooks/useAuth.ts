/**
 * useAuth Hook
 * Primary hook for authentication state and methods
 * 
 * @example
 * const { user, profile, isLoading, signIn, signOut } = useAuth();
 */

'use client';

import { useContext } from 'react';
import { AuthContext } from '../components/AuthProvider';
import type { AuthContextValue } from '../types/auth';

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error(
      'useAuth must be used within an AuthProvider. ' +
      'Wrap your app with <AuthProvider> in your root layout.'
    );
  }
  
  return context;
}
