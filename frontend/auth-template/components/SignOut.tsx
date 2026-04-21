/**
 * SignOut Component
 * Simple logout button
 * 
 * @example
 * <SignOut />
 * 
 * @example
 * <SignOut redirectTo="/" className="my-btn">Logout</SignOut>
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../hooks/useAuth';

interface SignOutProps {
  /** Where to redirect after logout */
  redirectTo?: string;
  /** Custom class name */
  className?: string;
  /** Button text */
  children?: React.ReactNode;
}

export function SignOut({
  redirectTo = '/auth/login',
  className = '',
  children = 'Sign Out',
}: SignOutProps) {
  const router = useRouter();
  const { signOut } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleSignOut = async () => {
    setIsLoading(true);
    await signOut();
    router.push(redirectTo);
  };

  return (
    <button
      onClick={handleSignOut}
      disabled={isLoading}
      className={`auth-signout ${className}`}
    >
      {isLoading ? 'Signing out...' : children}
    </button>
  );
}
