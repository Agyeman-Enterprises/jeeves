import { NextRequest, NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabase/server';
import { openIncidentManual } from '@/lib/jarvis/incidents/engine';

// GET: list incidents
// Query params:
//  - workspaceId (required)
//  - status (optional)
//  - limit (optional, default 50)
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const workspaceId = url.searchParams.get('workspaceId');
    const status = url.searchParams.get('status');
    const limitParam = url.searchParams.get('limit');
    const limit = limitParam ? Number(limitParam) : 50;

    if (!workspaceId) {
      return NextResponse.json(
        { ok: false, error: 'workspaceId is required' },
        { status: 400 }
      );
    }

    // TODO: enforce workspace-level authorization

    const supabase = supabaseServer;
    let query = (supabase as any)
      .from('jarvis_incidents')
      .select('*')
      .eq('workspace_id', workspaceId)
      .order('opened_at', { ascending: false })
      .limit(limit);

    if (status) {
      query = query.eq('status', status);
    }

    const { data, error } = await query;

    if (error) {
      console.error('[Incidents] GET /api/jarvis/incidents query error:', error);
      return NextResponse.json(
        { ok: false, error: 'Database error' },
        { status: 500 }
      );
    }

    return NextResponse.json({ ok: true, data });
  } catch (err) {
    console.error('[Incidents] GET /api/jarvis/incidents error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

// POST: open manual incident
// Body:
// {
//   "workspaceId": "...",
//   "title": "string",
//   "severity": "low|medium|high|critical",
//   "description": "optional",
//   "context": {...},
//   "playbookId": "optional"
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

    const { workspaceId, title, severity, description, context, playbookId } = body;

    if (!workspaceId || typeof workspaceId !== 'string') {
      return NextResponse.json(
        { ok: false, error: 'workspaceId is required' },
        { status: 400 }
      );
    }

    if (!title || typeof title !== 'string') {
      return NextResponse.json(
        { ok: false, error: 'title is required' },
        { status: 400 }
      );
    }

    // TODO: enforce workspace-level authorization

    const incident = await openIncidentManual({
      workspaceId,
      title,
      severity,
      description,
      context,
      playbookId
    });

    if (!incident) {
      return NextResponse.json(
        { ok: false, error: 'Failed to create incident' },
        { status: 500 }
      );
    }

    return NextResponse.json({ ok: true, data: incident });
  } catch (err) {
    console.error('[Incidents] POST /api/jarvis/incidents error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

