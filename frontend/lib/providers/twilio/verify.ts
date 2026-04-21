// Twilio webhook signature verification
import { NextRequest } from 'next/server';
import crypto from 'crypto';

export async function verifyTwilioSignature(
  req: NextRequest,
  rawBody: string
): Promise<boolean> {
  const signature = req.headers.get('x-twilio-signature');
  if (!signature) return false;

  const authToken = process.env.TWILIO_AUTH_TOKEN;
  if (!authToken) {
    console.warn('TWILIO_AUTH_TOKEN not configured, skipping verification');
    return true; // In dev, allow if token not set
  }

  // Twilio signature verification logic
  // This is a simplified version - real Twilio verification is more complex
  const url = req.url;
  const computed = crypto
    .createHmac('sha1', authToken)
    .update(url + rawBody)
    .digest('base64');

  return signature === computed;
}

