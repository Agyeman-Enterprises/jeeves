// Ghexit webhook signature verification
import { NextRequest } from 'next/server';
import crypto from 'crypto';

export async function verifyGhexitSignature(
  req: NextRequest,
  rawBody: string
): Promise<boolean> {
  const signature = req.headers.get('ghexit-signature');
  if (!signature) return false;

  const secret = process.env.GHEXIT_WEBHOOK_SECRET;
  if (!secret) {
    console.warn('GHEXIT_WEBHOOK_SECRET not configured, skipping verification');
    return true; // In dev, allow if secret not set
  }

  const computed = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');

  return signature === computed;
}

