import { NextRequest, NextResponse } from 'next/server';
import {
  evaluateAgentRulesForWorkspace,
  evaluateAgentRulesForAllWorkspaces
} from '@/lib/jarvis/agents/evaluator';

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const workspaceId = url.searchParams.get('workspaceId');

    // TODO: secure cron endpoint

    if (workspaceId) {
      const res = await evaluateAgentRulesForWorkspace(workspaceId);
      return NextResponse.json({ ok: true, scope: 'workspace', workspaceId, ...res });
    }

    const res = await evaluateAgentRulesForAllWorkspaces();
    return NextResponse.json({ ok: true, scope: 'all', ...res });
  } catch (err) {
    console.error('[IT12] cron error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal error' },
      { status: 500 }
    );
  }
}

