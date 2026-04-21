/**
 * SignIn Component
 * Email/password login form with validation
 * 
 * @example
 * <SignIn redirectTo="/dashboard" />
 * 
 * @example
 * // With custom styling
 * <SignIn 
 *   redirectTo="/dashboard"
 *   className="my-custom-class"
 *   showForgotPassword={true}
 * />
 */

'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../hooks/useAuth';

interface SignInProps {
  /** Where to redirect after successful login */
  redirectTo?: string;
  /** Show forgot password link */
  showForgotPassword?: boolean;
  /** Show sign up link */
  showSignUpLink?: boolean;
  /** Custom class name for the form container */
  className?: string;
  /** Callback on successful login */
  onSuccess?: () => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

export function SignIn({
  redirectTo = '/dashboard',
  showForgotPassword = true,
  showSignUpLink = true,
  className = '',
  onSuccess,
  onError,
}: SignInProps) {
  const router = useRouter();
  const { signIn } = useAuth();
  
  const [email, setEmail] = useState(() => {
    // Restore remembered email if available
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_remembered_email') || '';
    }
    return '';
  });
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_remember_me') === 'true';
    }
    return false;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Validation
  const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const isValidPassword = password.length >= 8;
  const canSubmit = isValidEmail && isValidPassword && !isLoading;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!canSubmit) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const { error: signInError } = await signIn(email, password);
      
      if (signInError) {
        // Generic error message - don't reveal if user exists
        setError('Invalid email or password');
        onError?.(signInError);
        return;
      }
      
      // Save or clear remembered email
      if (rememberMe) {
        localStorage.setItem('auth_remembered_email', email);
        localStorage.setItem('auth_remember_me', 'true');
      } else {
        localStorage.removeItem('auth_remembered_email');
        localStorage.removeItem('auth_remember_me');
      }

      onSuccess?.();
      router.push(redirectTo);
    } catch (err) {
      setError('An unexpected error occurred');
      onError?.(err as Error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`auth-signin ${className}`}>
      <form onSubmit={handleSubmit} className="auth-form" data-lpignore="true" data-1p-ignore="true">
        <h2 className="auth-title">Sign In</h2>
        
        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}
        
        <div className="auth-field">
          <label htmlFor="email" className="auth-label">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            autoComplete="username"
            autoCorrect="off"
            autoCapitalize="off"
            spellCheck={false}
            data-lpignore="true"
            data-1p-ignore="true"
            data-form-type="other"
            className="auth-input"
          />
        </div>
        
        <div className="auth-field">
          <label htmlFor="password" className="auth-label">
            Password
          </label>
          <div className="auth-password-wrapper">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              minLength={8}
              autoComplete="current-password"
              data-lpignore="true"
              data-1p-ignore="true"
              data-form-type="other"
              className="auth-input"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="auth-password-toggle"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>
        
        <div className="auth-field auth-remember">
          <label className="auth-checkbox-label">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="auth-checkbox"
            />
            <span>Remember me</span>
          </label>
        </div>

        <button
          type="submit"
          disabled={!canSubmit}
          className="auth-submit"
        >
          {isLoading ? 'Signing in...' : 'Sign In'}
        </button>
        
        <div className="auth-links">
          {showForgotPassword && (
            <a href="/auth/forgot-password" className="auth-link">
              Forgot password?
            </a>
          )}
          {showSignUpLink && (
            <a href="/auth/signup" className="auth-link">
              Don't have an account? Sign up
            </a>
          )}
        </div>
      </form>
    </div>
  );
}
