import { NextRequest, NextResponse } from "next/server";

// JJ proxy — forwards all /api/proxy/* requests to JJ backend (port 4004)
const BACKEND = process.env.JARVIS_BACKEND_URL ?? "http://localhost:4004";
const JARVIS_API_KEY = process.env.JARVIS_API_KEY ?? "";

function authHeaders(): Record<string, string> {
  return JARVIS_API_KEY ? { Authorization: `Bearer ${JARVIS_API_KEY}` } : {};
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path: pathSegments } = await params;
  const path = pathSegments.join("/");
  const url = `${BACKEND}/${path}${request.nextUrl.search}`;
  try {
    const r = await fetch(url, {
      headers: authHeaders(),
      cache: "no-store",
      signal: AbortSignal.timeout(90000),
    });
    const data = await r.json();
    return NextResponse.json(data, { status: r.status });
  } catch {
    return NextResponse.json({ error: "Backend unreachable" }, { status: 503 });
  }
}

async function proxyWithBody(
  method: string,
  request: NextRequest,
  params: Promise<{ path: string[] }>
): Promise<NextResponse> {
  const { path: pathSegments } = await params;
  const path = pathSegments.join("/");
  const url = `${BACKEND}/${path}`;
  try {
    const body = await request.json().catch(() => ({}));
    const r = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(body),
      cache: "no-store",
      signal: AbortSignal.timeout(90000),
    });
    const data = await r.json();
    return NextResponse.json(data, { status: r.status });
  } catch {
    return NextResponse.json({ error: "Backend unreachable" }, { status: 503 });
  }
}

export async function POST(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return proxyWithBody("POST", request, ctx.params);
}

export async function PATCH(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return proxyWithBody("PATCH", request, ctx.params);
}

export async function DELETE(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return proxyWithBody("DELETE", request, ctx.params);
}

export async function PUT(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  return proxyWithBody("PUT", request, ctx.params);
}
