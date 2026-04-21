import { NextRequest, NextResponse } from 'next/server';
import { ingestRecentProviderEvents } from '@/lib/jarvis/pim/ingest';

// IT-10A: Cron endpoint to ingest recent provider events into PIM.
// Protect this route with whatever auth / secret scheme you use for internal cron.
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const minutesParam = url.searchParams.get('minutes');
    const windowMinutes = minutesParam ? Number(minutesParam) : 10;

    // TODO: add authentication/authorization for internal cron usage
    const result = await ingestRecentProviderEvents(windowMinutes);

    return NextResponse.json({
      ok: true,
      windowMinutes,
      ...result
    });
  } catch (err) {
    console.error('[PIM] /api/internal/cron/pim-ingest error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

