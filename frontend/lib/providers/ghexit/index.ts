// Ghexit provider adapter
import { verifyGhexitSignature } from './verify';
import { normalizeGhexit } from './normalize';
import type { ProviderAdapter } from '../types';

export const GhexitAdapter: ProviderAdapter = {
  verify: verifyGhexitSignature,
  normalize: normalizeGhexit,
};

