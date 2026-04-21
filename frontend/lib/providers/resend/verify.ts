// Resend webhook signature verification
import { NextRequest } from 'next/server';
import crypto from 'crypto';

export async function verifyResendSignature(
  req: NextRequest,
  rawBody: string
): Promise<boolean> {
  const signature = req.headers.get('resend-signature');
  if (!signature) return false;

  const secret = process.env.RESEND_WEBHOOK_SECRET;
  if (!secret) {
    console.warn('RESEND_WEBHOOK_SECRET not configured, skipping verification');
    return true; // In dev, allow if secret not set
  }

  const computed = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');

  return signature === computed;
}

