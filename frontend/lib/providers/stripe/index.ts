// Stripe provider adapter
import { verifyStripeSignature } from './verify';
import { normalizeStripe } from './normalize';
import type { ProviderAdapter } from '../types';

export const StripeAdapter: ProviderAdapter = {
  verify: verifyStripeSignature,
  normalize: normalizeStripe,
};

