import { NextRequest, NextResponse } from 'next/server';
import { predictWorkspaceSpend } from '@/lib/jarvis/prediction/engine';

// IT-10C: Spend/volume prediction API
// GET params: workspaceId, horizonDays
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const workspaceId = url.searchParams.get('workspaceId');
    const horizonDaysParam = url.searchParams.get('horizonDays');
    const horizonDays = horizonDaysParam ? Number(horizonDaysParam) : 7;

    if (!workspaceId) {
      return NextResponse.json(
        { ok: false, error: 'workspaceId is required' },
        { status: 400 }
      );
    }

    // TODO: enforce auth/access control for workspaceId

    const result = await predictWorkspaceSpend({
      workspaceId,
      horizonDays
    });

    return NextResponse.json({ ok: true, data: result });
  } catch (err) {
    console.error('[Prediction] /api/jarvis/prediction/spend error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

