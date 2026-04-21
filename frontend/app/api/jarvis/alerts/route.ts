import { NextRequest, NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabase/server';

// IT-11: Public API to list alert events for a workspace.
// GET params:
// - workspaceId (required)
// - since (optional ISO datetime)
// - limit (optional, default 50)
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const workspaceId = url.searchParams.get('workspaceId');
    const since = url.searchParams.get('since');
    const limitParam = url.searchParams.get('limit');
    const limit = limitParam ? Number(limitParam) : 50;

    if (!workspaceId) {
      return NextResponse.json(
        { ok: false, error: 'workspaceId is required' },
        { status: 400 }
      );
    }

    // TODO: enforce that the caller is authorized to access this workspaceId

    const supabase = supabaseServer;

    let query = (supabase as any)
      .from('jarvis_alert_events')
      .select('*')
      .eq('workspace_id', workspaceId)
      .order('triggered_at', { ascending: false })
      .limit(limit);

    if (since) {
      query = query.gte('triggered_at', since);
    }

    const { data, error } = await query;

    if (error) {
      console.error('[Alerts] /api/jarvis/alerts query error:', error);
      return NextResponse.json(
        { ok: false, error: 'Database error' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      ok: true,
      data
    });
  } catch (err) {
    console.error('[Alerts] /api/jarvis/alerts error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

