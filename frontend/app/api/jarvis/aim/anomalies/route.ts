import { NextRequest, NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabase/server';
import { AIMEntityType } from '@/lib/jarvis/aim/types';

// IT-10B: Public API to fetch AIM anomalies.
// Query params:
// - workspaceId (required)
// - entityType ('user' | 'workspace', optional)
// - entityId (optional, if entityType='user')
// - since (optional ISO datetime)
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const workspaceId = url.searchParams.get('workspaceId');
    const entityType = url.searchParams.get('entityType') as AIMEntityType | null;
    const entityId = url.searchParams.get('entityId');
    const since = url.searchParams.get('since');

    if (!workspaceId) {
      return NextResponse.json(
        { ok: false, error: 'workspaceId is required' },
        { status: 400 }
      );
    }

    // TODO: enforce that the caller is authorized to access this workspaceId

    const supabase = supabaseServer;

    let query = (supabase as any)
      .from('jarvis_aim_anomalies')
      .select('*')
      .eq('workspace_id', workspaceId)
      .order('detected_at', { ascending: false });

    if (entityType) {
      query = query.eq('entity_type', entityType);
    }

    if (entityType === 'user' && entityId) {
      query = query.eq('entity_id', entityId);
    }

    if (since) {
      query = query.gte('detected_at', since);
    }

    const { data, error } = await query;
    if (error) {
      console.error('[AIM] anomalies query error:', error);
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
    console.error('[AIM] /api/jarvis/aim/anomalies error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

