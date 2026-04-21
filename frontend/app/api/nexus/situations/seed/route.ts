// API endpoint to seed default situation room for a workspace
import { NextRequest, NextResponse } from 'next/server';
import { createDefaultSituationRoom } from '@/lib/nexus/situations/seed';

export async function POST(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const workspaceId = searchParams.get('workspaceId');
    const userId = searchParams.get('userId');

    if (!workspaceId || !userId) {
      return NextResponse.json(
        { error: 'workspaceId and userId are required as query parameters' },
        { status: 400 }
      );
    }

    const room = await createDefaultSituationRoom(workspaceId, userId);
    
    return NextResponse.json(
      { 
        success: true, 
        room,
        message: 'Default situation room created successfully' 
      },
      { status: 201 }
    );
  } catch (err: any) {
    console.error('Seed situation room error', err);
    return NextResponse.json(
      { error: err?.message || 'Failed to create default situation room' },
      { status: 500 }
    );
  }
}

