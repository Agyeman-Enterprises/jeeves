import { NextRequest, NextResponse } from "next/server";
import { runSelfAudit, runAllAudits } from "@/lib/jarvis/refactor/audit";
import type { AuditType } from "@/lib/jarvis/refactor/types";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { audit_type, all } = body;
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    if (all) {
      // Run all audits
      const auditIds = await runAllAudits(userId);
      return NextResponse.json({ ok: true, audit_ids: auditIds });
    }

    if (!audit_type) {
      return NextResponse.json(
        { error: "Missing audit_type (or set all=true)" },
        { status: 400 }
      );
    }

    const auditId = await runSelfAudit(userId, audit_type as AuditType);

    return NextResponse.json({ ok: true, audit_id: auditId });
  } catch (error: any) {
    console.error("Self-audit error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

