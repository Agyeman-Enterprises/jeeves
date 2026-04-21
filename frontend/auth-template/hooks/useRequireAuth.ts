/**
 * useRequireAuth Hook
 * Redirects to login if not authenticated
 * 
 * @example
 * // In a protected page component
 * const { user, profile } = useRequireAuth();
 * // Will redirect to /auth/login if not authenticated
 * 
 * @example
 * // With custom redirect
 * const { user } = useRequireAuth({ redirectTo: '/signin' });
 * 
 * @example
 * // With role requirement
 * const { user } = useRequireAuth({ requiredRole: 'admin' });
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from './useAuth';
import { hasRole, hasAnyRole } from '../utils/roles';
import type { UserRole } from '../types/auth';

interface UseRequireAuthOptions {
  redirectTo?: string;
  requiredRole?: UserRole;
  allowedRoles?: UserRole[];
}

export function useRequireAuth(options: UseRequireAuthOptions = {}) {
  const {
    redirectTo = '/auth/login',
    requiredRole,
    allowedRoles,
  } = options;
  
  const router = useRouter();
  const auth = useAuth();
  const { user, profile, isLoading } = auth;
  
  useEffect(() => {
    if (isLoading) return;
    
    // Not authenticated - redirect to login
    if (!user) {
      const currentPath = window.location.pathname;
      const loginUrl = `${redirectTo}?redirect=${encodeURIComponent(currentPath)}`;
      router.replace(loginUrl);
      return;
    }
    
    // Check role requirement
    if (requiredRole && profile && !hasRole(profile.role, requiredRole)) {
      router.replace('/auth/unauthorized');
      return;
    }
    
    // Check allowed roles
    if (allowedRoles && profile && !hasAnyRole(profile.role, allowedRoles)) {
      router.replace('/auth/unauthorized');
      return;
    }
  }, [user, profile, isLoading, router, redirectTo, requiredRole, allowedRoles]);
  
  return auth;
}
