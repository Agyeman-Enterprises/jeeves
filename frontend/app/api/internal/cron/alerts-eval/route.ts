import { NextRequest, NextResponse } from 'next/server';
import {
  evaluateAlertsForWorkspace,
  evaluateAlertsForAllWorkspaces
} from '@/lib/jarvis/alerts/evaluator';

// IT-11: Cron endpoint to evaluate alert rules.
// GET params:
// - workspaceId (optional): if present, only evaluate that workspace.
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const workspaceId = url.searchParams.get('workspaceId');

    // TODO: add authentication/authorization for internal cron usage

    if (workspaceId) {
      const result = await evaluateAlertsForWorkspace(workspaceId);
      return NextResponse.json({
        ok: true,
        scope: 'workspace',
        workspaceId,
        ...result
      });
    } else {
      const result = await evaluateAlertsForAllWorkspaces();
      return NextResponse.json({
        ok: true,
        scope: 'all',
        ...result
      });
    }
  } catch (err) {
    console.error('[Alerts] /api/internal/cron/alerts-eval error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

