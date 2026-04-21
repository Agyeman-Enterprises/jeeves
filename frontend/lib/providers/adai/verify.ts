// AdAI/Meta webhook signature verification
import { NextRequest } from 'next/server';
import crypto from 'crypto';

/**
 * Verify Meta webhook signature
 * Meta uses X-Hub-Signature-256 header with HMAC-SHA256
 * @see https://developers.facebook.com/docs/graph-api/webhooks/getting-started#verification-requests
 */
export async function verifyAdAISignature(
  req: NextRequest,
  rawBody: string
): Promise<boolean> {
  const signature = req.headers.get('x-hub-signature-256');

  // For internal AdAI events (from Cloudflare Worker), check our custom header
  const internalSignature = req.headers.get('x-adai-signature');

  if (internalSignature) {
    return verifyInternalSignature(internalSignature, rawBody);
  }

  if (!signature) {
    console.warn('No signature header found for AdAI webhook');
    return false;
  }

  const secret = process.env.META_APP_SECRET;
  if (!secret) {
    console.warn('META_APP_SECRET not configured, skipping verification');
    // In dev, allow if secret not set
    return process.env.NODE_ENV === 'development';
  }

  // Meta signature format: sha256=<hash>
  const [algorithm, expectedHash] = signature.split('=');
  if (algorithm !== 'sha256') {
    console.warn(`Unexpected signature algorithm: ${algorithm}`);
    return false;
  }

  const computed = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(expectedHash),
    Buffer.from(computed)
  );
}

/**
 * Verify internal AdAI signature (from Cloudflare Worker)
 */
function verifyInternalSignature(signature: string, rawBody: string): boolean {
  const secret = process.env.ADAI_INTERNAL_SECRET;
  if (!secret) {
    console.warn('ADAI_INTERNAL_SECRET not configured');
    return process.env.NODE_ENV === 'development';
  }

  const computed = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(computed)
  );
}
