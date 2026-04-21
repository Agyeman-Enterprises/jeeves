/**
 * Role Utilities
 * CUSTOMIZE: Add role hierarchies and permissions for your app
 */

import { UserRole } from '../types/auth';

// ============================================================================
// CUSTOMIZE THESE FOR YOUR APP
// ============================================================================

/**
 * Role hierarchy (higher index = more permissions)
 * Roles can access their level and below
 */
const ROLE_HIERARCHY: Record<UserRole, number> = {
  user: 0,
  staff: 1,
  admin: 2,
};

/**
 * Role display names
 */
export const ROLE_DISPLAY_NAMES: Record<UserRole, string> = {
  user: 'User',
  staff: 'Staff',
  admin: 'Administrator',
};

/**
 * Default redirect path after login for each role
 */
export const ROLE_HOME_PATHS: Record<UserRole, string> = {
  user: '/dashboard',
  staff: '/dashboard',
  admin: '/admin',
};

// ============================================================================
// ROLE HELPER FUNCTIONS (generally don't need to modify)
// ============================================================================

/**
 * Check if a role string is valid
 */
export function isValidRole(role: unknown): role is UserRole {
  return typeof role === 'string' && UserRole.includes(role as UserRole);
}

/**
 * Normalize role string to canonical form
 * Handles legacy/alternate role names
 */
export function normalizeRole(role: unknown): UserRole | null {
  if (!role || typeof role !== 'string') return null;
  
  const lower = role.toLowerCase().trim();
  
  // Direct match
  if (isValidRole(lower)) return lower;
  
  // Legacy mappings - ADD YOUR OWN as needed
  const LEGACY_MAPPINGS: Record<string, UserRole> = {
    administrator: 'admin',
    superuser: 'admin',
    employee: 'staff',
    member: 'user',
    customer: 'user',
  };
  
  return LEGACY_MAPPINGS[lower] ?? null;
}

/**
 * Check if user has a specific role
 */
export function hasRole(userRole: unknown, requiredRole: UserRole): boolean {
  const normalized = normalizeRole(userRole);
  return normalized === requiredRole;
}

/**
 * Check if user has any of the specified roles
 */
export function hasAnyRole(userRole: unknown, allowedRoles: UserRole[]): boolean {
  const normalized = normalizeRole(userRole);
  if (!normalized) return false;
  return allowedRoles.includes(normalized);
}

/**
 * Check if user's role meets minimum level (uses hierarchy)
 */
export function hasMinimumRole(userRole: unknown, minimumRole: UserRole): boolean {
  const normalized = normalizeRole(userRole);
  if (!normalized) return false;
  
  const userLevel = ROLE_HIERARCHY[normalized] ?? -1;
  const requiredLevel = ROLE_HIERARCHY[minimumRole] ?? 999;
  
  return userLevel >= requiredLevel;
}

/**
 * Get home path for a role
 */
export function getHomePathForRole(role: unknown): string {
  const normalized = normalizeRole(role);
  if (!normalized) return '/';
  return ROLE_HOME_PATHS[normalized] ?? '/dashboard';
}

/**
 * Get display name for a role
 */
export function getRoleDisplayName(role: unknown): string {
  const normalized = normalizeRole(role);
  if (!normalized) return 'Unknown';
  return ROLE_DISPLAY_NAMES[normalized] ?? normalized;
}
