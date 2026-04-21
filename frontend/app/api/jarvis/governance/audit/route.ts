import { NextRequest, NextResponse } from "next/server";
import { getAuditLogs } from "@/lib/jarvis/governance/audit";
import type { ComplianceFlag } from "@/lib/jarvis/governance/types";

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const searchParams = req.nextUrl.searchParams;
    const filters = {
      domain: searchParams.get("domain") || undefined,
      agent_slug: searchParams.get("agent_slug") || undefined,
      patient_id: searchParams.get("patient_id") || undefined,
      entity_id: searchParams.get("entity_id") || undefined,
      compliance_flag: (searchParams.get("compliance_flag") as ComplianceFlag) || undefined,
      start_date: searchParams.get("start_date") || undefined,
      end_date: searchParams.get("end_date") || undefined,
      limit: searchParams.get("limit") ? parseInt(searchParams.get("limit")!) : undefined,
    };

    const logs = await getAuditLogs(userId, filters);

    return NextResponse.json({ logs });
  } catch (error: any) {
    console.error("Get audit logs error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

