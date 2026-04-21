import { NextRequest, NextResponse } from 'next/server';
import { getPIMHealthSnapshot } from '@/lib/jarvis/pim/health';
import { ProviderChannel } from '@/lib/jarvis/pim/types';

// IT-10A: Public API for Provider Health Snapshot.
// Expects query params: workspaceId, provider, channel, windowHours.
// Assumes existing auth/session enforcement in your API stack; adapt as needed.
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const workspaceId = url.searchParams.get('workspaceId');
    const provider = url.searchParams.get('provider') ?? 'ghexit';
    const channel = (url.searchParams.get('channel') ?? 'sms') as ProviderChannel;
    const windowHoursParam = url.searchParams.get('windowHours');
    const windowHours = windowHoursParam ? Number(windowHoursParam) : 24;

    if (!workspaceId) {
      return NextResponse.json(
        { ok: false, error: 'workspaceId is required' },
        { status: 400 }
      );
    }

    // TODO: enforce that the caller is authorized to access this workspaceId

    const snapshot = await getPIMHealthSnapshot({
      workspaceId,
      provider,
      channel,
      windowHours
    });

    return NextResponse.json({ ok: true, data: snapshot });
  } catch (err) {
    console.error('[PIM] /api/jarvis/pim/health error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

