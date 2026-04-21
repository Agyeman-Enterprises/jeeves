// Resend provider adapter
import { verifyResendSignature } from './verify';
import { normalizeResend } from './normalize';
import type { ProviderAdapter } from '../types';

export const ResendAdapter: ProviderAdapter = {
  verify: verifyResendSignature,
  normalize: normalizeResend,
};

