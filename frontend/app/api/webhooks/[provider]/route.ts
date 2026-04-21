// src/app/api/webhooks/[provider]/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { emitEvent } from '@/lib/jarvis/events/gem/bus';
import { getProviderAdapter } from '@/lib/providers/registry';

type Provider = 'stripe' | 'twilio' | 'resend' | 'ghexit' | 'custom';

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ provider: string }> }
) {
  const { provider: providerParam } = await params;
  const provider = providerParam as Provider;

  const rawBody = await req.text();
  
  // Parse JSON payload
  let payload: any;
  try {
    payload = JSON.parse(rawBody || '{}');
  } catch {
    payload = { raw: rawBody };
  }

  // Get provider adapter
  const adapter = getProviderAdapter(provider);
  if (!adapter) {
    return NextResponse.json(
      { error: `Unknown provider: ${provider}` },
      { status: 400 }
    );
  }

  // Verify signature
  const verified = await adapter.verify(req, rawBody);
  if (!verified) {
    return NextResponse.json(
      { error: 'signature verification failed' },
      { status: 401 }
    );
  }

  // Normalize event
  const normalized = adapter.normalize(payload);

  // Validate required fields
  if (!normalized.workspaceId || !normalized.userId) {
    return NextResponse.json(
      { error: 'workspaceId and userId are required (in body or metadata)' },
      { status: 400 }
    );
  }

  // Emit to GEM
  try {
    const saved = await emitEvent({
      type: `external.provider.${normalized.provider}.${normalized.type}` as any,
      source: 'external.webhook',
      workspaceId: normalized.workspaceId,
      userId: normalized.userId,
      subjectId: normalized.subjectId,
      payload: {
        workspaceId: normalized.workspaceId,
        userId: normalized.userId,
        location: `webhook.${normalized.provider}`,
        message: `Provider event: ${normalized.provider}.${normalized.type}`,
        stack: JSON.stringify(normalized.payload).slice(0, 8000),
        providerData: normalized.payload,
      },
    });

    return NextResponse.json({ ok: true, eventId: saved.id }, { status: 200 });
  } catch (err) {
    console.error('Webhook -> GEM error', err);
    return NextResponse.json(
      { error: 'Failed to process webhook' },
      { status: 500 }
    );
  }
}
