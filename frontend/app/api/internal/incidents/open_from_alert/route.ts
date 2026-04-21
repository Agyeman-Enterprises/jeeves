import { NextRequest, NextResponse } from 'next/server';
import { openIncidentFromAlert } from '@/lib/jarvis/incidents/engine';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => null);
    if (!body || typeof body !== 'object') {
      return NextResponse.json(
        { ok: false, error: 'Invalid JSON body' },
        { status: 400 }
      );
    }

    const { workspaceId, alertId } = body;

    if (!workspaceId || typeof workspaceId !== 'string') {
      return NextResponse.json(
        { ok: false, error: 'workspaceId is required' },
        { status: 400 }
      );
    }

    if (!alertId || typeof alertId !== 'string') {
      return NextResponse.json(
        { ok: false, error: 'alertId is required' },
        { status: 400 }
      );
    }

    // TODO: auth for internal usage

    const incident = await openIncidentFromAlert({ workspaceId, alertId });

    if (!incident) {
      return NextResponse.json(
        { ok: false, error: 'Failed to create incident from alert' },
        { status: 500 }
      );
    }

    return NextResponse.json({ ok: true, data: incident });
  } catch (err) {
    console.error('[Incidents] POST /api/internal/incidents/open_from_alert error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

