// Provider registry - central registry for all webhook providers
import { GhexitAdapter } from './ghexit';
import { TwilioAdapter } from './twilio';
import { ResendAdapter } from './resend';
import { StripeAdapter } from './stripe';
import { AdAIAdapter } from './adai';
import type { ProviderAdapter } from './types';

export const providerRegistry: Record<string, ProviderAdapter> = {
  ghexit: GhexitAdapter,
  twilio: TwilioAdapter,
  resend: ResendAdapter,
  stripe: StripeAdapter,
  adai: AdAIAdapter,
};

export function getProviderAdapter(provider: string): ProviderAdapter | null {
  return providerRegistry[provider] || null;
}

