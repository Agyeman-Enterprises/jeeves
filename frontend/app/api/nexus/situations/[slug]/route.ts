// src/app/api/nexus/situations/[slug]/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getSituationRoomBySlug } from '@/lib/nexus/situations/service';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params;
  const { searchParams } = new URL(req.url);
  const workspaceId = searchParams.get('workspaceId');

  if (!workspaceId) {
    return NextResponse.json({ error: 'workspaceId is required' }, { status: 400 });
  }

  try {
    const result = await getSituationRoomBySlug(workspaceId, slug);
    if (!result.room) {
      return NextResponse.json({ error: 'Not found' }, { status: 404 });
    }

    return NextResponse.json(result, { status: 200 });
  } catch (err) {
    console.error('Situation room GET error', err);
    return NextResponse.json({ error: 'Failed to load situation room' }, { status: 500 });
  }
}

