import { NextRequest, NextResponse } from 'next/server';
import { computeRoutingRecommendation } from '@/lib/jarvis/prediction/engine';

// IT-10C: Routing recommendation API
// GET params: workspaceId, provider, channel
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const workspaceId = url.searchParams.get('workspaceId');
    const provider = url.searchParams.get('provider') ?? 'ghexit';
    const channel = url.searchParams.get('channel') ?? 'sms';

    if (!workspaceId) {
      return NextResponse.json(
        { ok: false, error: 'workspaceId is required' },
        { status: 400 }
      );
    }

    // TODO: enforce auth/access control for workspaceId

    const result = await computeRoutingRecommendation({
      workspaceId,
      provider,
      channel
    });

    return NextResponse.json({ ok: true, data: result });
  } catch (err) {
    console.error('[Prediction] /api/jarvis/prediction/routing error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

