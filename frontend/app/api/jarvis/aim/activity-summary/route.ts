import { NextRequest, NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabase/server';

// IT-10B: Public API to fetch AIM activity summaries.
// Query params:
// - workspaceId (required)
// - userId (optional: if present, return per-user daily records; else per-workspace cycles)
// - from (optional ISO date, inclusive)
// - to (optional ISO date, inclusive)
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const workspaceId = url.searchParams.get('workspaceId');
    const userId = url.searchParams.get('userId');
    const from = url.searchParams.get('from');
    const to = url.searchParams.get('to');

    if (!workspaceId) {
      return NextResponse.json(
        { ok: false, error: 'workspaceId is required' },
        { status: 400 }
      );
    }

    // TODO: enforce that the caller is authorized to access this workspaceId

    const supabase = supabaseServer;

    if (userId) {
      // user-level activity
      let query = (supabase as any)
        .from('jarvis_aim_user_activity')
        .select('*')
        .eq('workspace_id', workspaceId)
        .eq('user_id', userId)
        .order('date_bucket', { ascending: true });

      if (from) {
        query = query.gte('date_bucket', from);
      }
      if (to) {
        query = query.lte('date_bucket', to);
      }

      const { data, error } = await query;
      if (error) {
        console.error('[AIM] activity-summary user query error:', error);
        return NextResponse.json(
          { ok: false, error: 'Database error' },
          { status: 500 }
        );
      }

      return NextResponse.json({
        ok: true,
        scope: 'user',
        data
      });
    } else {
      // workspace-level cycles
      let query = (supabase as any)
        .from('jarvis_aim_enterprise_cycles')
        .select('*')
        .eq('workspace_id', workspaceId)
        .order('date_bucket', { ascending: true });

      if (from) {
        query = query.gte('date_bucket', from);
      }
      if (to) {
        query = query.lte('date_bucket', to);
      }

      const { data, error } = await query;
      if (error) {
        console.error('[AIM] activity-summary workspace query error:', error);
        return NextResponse.json(
          { ok: false, error: 'Database error' },
          { status: 500 }
        );
      }

      return NextResponse.json({
        ok: true,
        scope: 'workspace',
        data
      });
    }
  } catch (err) {
    console.error('[AIM] /api/jarvis/aim/activity-summary error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

