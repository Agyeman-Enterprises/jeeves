import { NextRequest, NextResponse } from 'next/server';
import { chooseRoutingProvider } from '@/lib/jarvis/routing/engine';

// IT-13: Routing decision API.
// POST body:
// {
//   "workspaceId": "uuid",
//   "channel": "sms",
//   "region": "us",     // optional
//   "requestId": "..."  // optional
// }

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => null);

    if (!body || typeof body !== 'object') {
      return NextResponse.json(
        { ok: false, error: 'Invalid JSON body' },
        { status: 400 }
      );
    }

    const { workspaceId, channel, region, requestId } = body;

    if (!workspaceId || typeof workspaceId !== 'string') {
      return NextResponse.json(
        { ok: false, error: 'workspaceId is required' },
        { status: 400 }
      );
    }

    if (!channel || typeof channel !== 'string') {
      return NextResponse.json(
        { ok: false, error: 'channel is required' },
        { status: 400 }
      );
    }

    // TODO: enforce auth/access control for workspaceId

    const decision = await chooseRoutingProvider({
      workspaceId,
      channel,
      region: typeof region === 'string' ? region : undefined,
      requestId: typeof requestId === 'string' ? requestId : undefined
    });

    return NextResponse.json({ ok: true, data: decision });
  } catch (err) {
    console.error('[Routing] /api/jarvis/routing/decide error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

