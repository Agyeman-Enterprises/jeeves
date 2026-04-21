import { NextRequest, NextResponse } from 'next/server';
import { predictProviderFailureRate } from '@/lib/jarvis/prediction/engine';

// IT-10C: Failure rate prediction API
// GET params: workspaceId, provider, channel, horizonHours
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const workspaceId = url.searchParams.get('workspaceId');
    const provider = url.searchParams.get('provider') ?? 'ghexit';
    const channel = url.searchParams.get('channel') ?? 'sms';
    const horizonHoursParam = url.searchParams.get('horizonHours');
    const horizonHours = horizonHoursParam ? Number(horizonHoursParam) : 24;

    if (!workspaceId) {
      return NextResponse.json(
        { ok: false, error: 'workspaceId is required' },
        { status: 400 }
      );
    }

    // TODO: enforce auth/access control for workspaceId

    const result = await predictProviderFailureRate({
      workspaceId,
      provider,
      channel,
      horizonHours
    });

    return NextResponse.json({ ok: true, data: result });
  } catch (err) {
    console.error('[Prediction] /api/jarvis/prediction/failures error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

