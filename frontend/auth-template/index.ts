/**
 * Auth Components Index
 * Import all components from here
 * 
 * @example
 * import { AuthProvider, SignIn, SignOut, useAuth } from '@/auth-template';
 */

// Components
export { AuthProvider, AuthContext } from './components/AuthProvider';
export { SignIn } from './components/SignIn';
export { SignUp } from './components/SignUp';
export { SignOut } from './components/SignOut';

// Hooks
export { useAuth } from './hooks/useAuth';
export { useSession } from './hooks/useSession';
export { useRequireAuth } from './hooks/useRequireAuth';

// Utils
export {
  isValidRole,
  normalizeRole,
  hasRole,
  hasAnyRole,
  hasMinimumRole,
  getHomePathForRole,
  getRoleDisplayName,
  ROLE_DISPLAY_NAMES,
  ROLE_HOME_PATHS,
} from './utils/roles';

// Types
export type {
  UserRole,
  UserProfile,
  AuthState,
  AuthContextValue,
  SignInFormData,
  SignUpFormData,
} from './types/auth';
