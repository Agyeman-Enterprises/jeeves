import { NextRequest, NextResponse } from 'next/server';
import { rollupRecentActivity, detectWorkspaceAnomaliesForRecentDay } from '@/lib/jarvis/aim/analyze';

// IT-10B: Cron endpoint to:
// 1) Roll up recent events into AIM tables.
// 2) Optionally run workspace anomaly detection.
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const minutesParam = url.searchParams.get('minutes');
    const runAnomaliesParam = url.searchParams.get('runAnomalies');

    const windowMinutes = minutesParam ? Number(minutesParam) : 10;
    const runAnomalies = runAnomaliesParam === 'true';

    // TODO: add authentication/authorization for internal cron usage

    const rollupResult = await rollupRecentActivity(windowMinutes);
    let anomalyResult: { workspacesChecked: number; anomaliesInserted: number } | null = null;

    if (runAnomalies) {
      anomalyResult = await detectWorkspaceAnomaliesForRecentDay(7);
    }

    return NextResponse.json({
      ok: true,
      windowMinutes,
      rollup: rollupResult,
      anomalies: anomalyResult
    });
  } catch (err) {
    console.error('[AIM] /api/internal/cron/aim-rollup error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

