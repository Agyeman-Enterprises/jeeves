import { NextRequest, NextResponse } from 'next/server';
import { runNextIncidentStep } from '@/lib/jarvis/incidents/engine';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => null);
    if (!body || typeof body !== 'object') {
      return NextResponse.json(
        { ok: false, error: 'Invalid JSON body' },
        { status: 400 }
      );
    }

    const { incidentId } = body;

    if (!incidentId || typeof incidentId !== 'string') {
      return NextResponse.json(
        { ok: false, error: 'incidentId is required' },
        { status: 400 }
      );
    }

    // TODO: auth for internal usage

    const { step, incident } = await runNextIncidentStep(incidentId);

    return NextResponse.json({
      ok: true,
      data: {
        step,
        incident
      }
    });
  } catch (err) {
    console.error('[Incidents] POST /api/internal/incidents/run_step error:', err);
    return NextResponse.json(
      { ok: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

