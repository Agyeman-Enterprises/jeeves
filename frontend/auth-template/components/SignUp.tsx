/**
 * SignUp Component
 * Registration form with email/password
 * Features: password visibility toggle, LastPass/1Password blocker
 */

'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../hooks/useAuth';

interface SignUpProps {
  redirectTo?: string;
  className?: string;
  onSuccess?: () => void;
}

export function SignUp({ redirectTo = '/auth/verify', className = '', onSuccess }: SignUpProps) {
  const router = useRouter();
  const { signUp } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const isValidPassword = password.length >= 8;
  const passwordsMatch = password === confirmPassword;
  const canSubmit = isValidEmail && isValidPassword && passwordsMatch && !isLoading;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setIsLoading(true);
    setError(null);

    const { error: signUpError } = await signUp(email, password);

    if (signUpError) {
      setError('Unable to create account. Please try again.');
      setIsLoading(false);
      return;
    }

    onSuccess?.();
    router.push(redirectTo);
  };

  return (
    <div className={`auth-signup ${className}`}>
      <form onSubmit={handleSubmit} className="auth-form" data-lpignore="true" data-1p-ignore="true">
        <h2 className="auth-title">Create Account</h2>

        {error && <div className="auth-error" role="alert">{error}</div>}

        <div className="auth-field">
          <label htmlFor="signup-email">Email</label>
          <input
            id="signup-email"
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
          <label htmlFor="signup-password">Password</label>
          <div className="auth-password-wrapper">
            <input
              id="signup-password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              required
              minLength={8}
              autoComplete="new-password"
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
          {password && !isValidPassword && (
            <span className="auth-hint">Password must be at least 8 characters</span>
          )}
        </div>

        <div className="auth-field">
          <label htmlFor="signup-confirmPassword">Confirm Password</label>
          <div className="auth-password-wrapper">
            <input
              id="signup-confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your password"
              required
              autoComplete="new-password"
              data-lpignore="true"
              data-1p-ignore="true"
              data-form-type="other"
              className="auth-input"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="auth-password-toggle"
              aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
            >
              {showConfirmPassword ? 'Hide' : 'Show'}
            </button>
          </div>
          {confirmPassword && !passwordsMatch && (
            <span className="auth-hint">Passwords do not match</span>
          )}
        </div>

        <button type="submit" disabled={!canSubmit} className="auth-submit">
          {isLoading ? 'Creating account...' : 'Sign Up'}
        </button>

        <a href="/auth/login" className="auth-link">
          Already have an account? Sign in
        </a>
      </form>
    </div>
  );
}
