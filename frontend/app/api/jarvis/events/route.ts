// src/app/api/jarvis/events/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { emitEvent } from '@/lib/jarvis/events/gem/bus';
import { JarvisEventEnvelope, JarvisEventType } from '@/lib/jarvis/events/gem/types';
import { supabaseServer } from '@/lib/supabase/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const events: JarvisEventEnvelope[] = Array.isArray(body)
      ? body
      : [body];

    const persisted: JarvisEventEnvelope[] = [];

    for (const ev of events) {
      // Basic validation
      if (!ev.type || !ev.workspaceId || !ev.userId || !ev.source || !ev.payload) {
        return NextResponse.json(
          { error: 'Invalid event: missing required fields' },
          { status: 400 }
        );
      }

      const saved = await emitEvent(ev as JarvisEventEnvelope<JarvisEventType>);
      persisted.push(saved);
    }

    return NextResponse.json({ events: persisted }, { status: 201 });
  } catch (err) {
    console.error('GEM POST error', err);
    return NextResponse.json(
      { error: 'Failed to ingest events' },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const workspaceId = searchParams.get('workspaceId');
  const type = searchParams.get('type');          // single type
  const types = searchParams.get('types');        // comma-separated list
  const since = searchParams.get('since');
  const subjectId = searchParams.get('subjectId');
  const correlationId = searchParams.get('correlationId');
  const limit = parseInt(searchParams.get('limit') || '50', 10);

  if (!workspaceId) {
    return NextResponse.json(
      { error: 'workspaceId is required' },
      { status: 400 }
    );
  }

  const client = supabaseServer;
  let query = client
    .from('jarvis_events')
    .select('*')
    .eq('workspace_id', workspaceId)
    .order('created_at', { ascending: false })
    .limit(limit) as any;

  if (type) {
    query = query.eq('event_type', type);
  }

  if (types) {
    const list = types.split(',').map((t) => t.trim()).filter(Boolean);
    if (list.length > 0) {
      query = query.in('event_type', list);
    }
  }

  if (since) {
    query = query.gte('created_at', since);
  }

  if (subjectId) {
    query = query.eq('subject_id', subjectId);
  }

  if (correlationId) {
    query = query.eq('correlation_id', correlationId);
  }

  const { data, error } = await query;

  if (error) {
    console.error('GEM GET error', error);
    return NextResponse.json(
      { error: 'Failed to fetch events' },
      { status: 500 }
    );
  }

  return NextResponse.json({ events: data }, { status: 200 });
}

