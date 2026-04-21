/**
 * TypeScript types for JarvisCore workspaces, tenants, and modules
 * Generated for Inov8if tenant registration
 */

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Workspace {
  id: string;
  tenant_id: string;
  owner_id: string;
  name: string;
  slug: string;
  description?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMember {
  id: string;
  workspace_id: string;
  user_id: string;
  role?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Module {
  id: string;
  workspace_id: string;
  tenant_id: string;
  name: string;
  slug: string;
  version?: string;
  description?: string;
  metadata?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Company {
  id: string;
  workspace_id: string;
  tenant_id?: string;
  name: string;
  domain?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Inov8if specific types
export interface Inov8ifTenant extends Tenant {
  slug: 'inov8if';
  name: 'Inov8if';
}

export interface Inov8ifWorkspace extends Workspace {
  slug: 'inov8if_medmaker' | 'inov8if_training_simulation' | 'inov8if_kraftforge';
  tenant_id: string; // Inov8if tenant ID
}

export type Inov8ifModuleSlug = 'medicore' | 'barebones' | 'rucucicast' | 'resusrunner';

export interface Inov8ifModule extends Module {
  slug: Inov8ifModuleSlug;
  workspace_id: string; // One of the Inov8if workspace IDs
}

// Workspace slugs
export const INOV8IF_WORKSPACE_SLUGS = {
  MEDMAKER: 'inov8if_medmaker',
  TRAINING_SIMULATION: 'inov8if_training_simulation',
  KRAFTFORGE: 'inov8if_kraftforge',
} as const;

// Module slugs
export const INOV8IF_MODULE_SLUGS = {
  MEDICORE: 'medicore',
  BAREBONES: 'barebones',
  RUCUCAST: 'rucucicast',
  RESUSRUNNER: 'resusrunner',
} as const;

// Company names
export const INOV8IF_COMPANIES = {
  INOV8IF: 'Inov8if',
  MEDMAKER: 'MedMaker',
  TRAINING_SIMULATION: 'Training & Simulation',
  KRAFTFORGE: 'KraftForge',
} as const;

