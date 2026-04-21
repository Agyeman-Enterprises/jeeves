// API endpoint for Situation Room metrics
import { NextRequest, NextResponse } from 'next/server';
import { getMetricValue } from '@/lib/nexus/situations/metrics';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const workspaceId = searchParams.get('workspaceId');
  const metric = searchParams.get('metric');

  if (!workspaceId || !metric) {
    return NextResponse.json(
      { error: 'workspaceId and metric are required' },
      { status: 400 }
    );
  }

  try {
    const value = await getMetricValue(workspaceId, metric);
    return NextResponse.json({ value }, { status: 200 });
  } catch (err) {
    console.error('Metrics GET error', err);
    return NextResponse.json(
      { error: 'Failed to fetch metric' },
      { status: 500 }
    );
  }
}

