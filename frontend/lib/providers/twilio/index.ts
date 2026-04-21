// Twilio provider adapter
import { verifyTwilioSignature } from './verify';
import { normalizeTwilio } from './normalize';
import type { ProviderAdapter } from '../types';

export const TwilioAdapter: ProviderAdapter = {
  verify: verifyTwilioSignature,
  normalize: normalizeTwilio,
};

