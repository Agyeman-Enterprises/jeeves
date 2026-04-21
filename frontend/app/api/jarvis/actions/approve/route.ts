import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";
import { executeAction } from "@/lib/jarvis/actions/executor";
import { selectPersona } from "@/lib/jarvis/persona/selector";
import type { PersonaContext } from "@/lib/jarvis/persona/types";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { approval_id, action } = body; // action: "approve" | "reject"
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId || !approval_id || !action) {
      return NextResponse.json(
        { error: "Missing required fields: user_id, approval_id, action" },
        { status: 400 }
      );
    }

    // Get approval request
    const { data: approval } = await supabaseServer
      .from("jarvis_action_approvals")
      .select("*")
      .eq("id", approval_id)
      .eq("user_id", userId)
      .eq("status", "PENDING")
      .single();

    if (!approval) {
      return NextResponse.json(
        { error: "Approval request not found or already processed" },
        { status: 404 }
      );
    }

    const appr = approval as any;

    // Update approval status
    const newStatus = action === "approve" ? "APPROVED" : "REJECTED";
    const approvalUpdate: Record<string, any> = {
      status: newStatus,
      reviewed_at: new Date().toISOString(),
    };
    await (supabaseServer as any)
      .from("jarvis_action_approvals")
      .update(approvalUpdate)
      .eq("id", approval_id);

    // Update action log
    const logUpdate: Record<string, any> = {
      status: action === "approve" ? "APPROVED" : "REJECTED",
      approved_by: action === "approve" ? userId : null,
      approved_at: action === "approve" ? new Date().toISOString() : null,
    };
    await (supabaseServer as any)
      .from("jarvis_action_logs")
      .update(logUpdate)
      .eq("id", appr.action_log_id);

    // If approved, execute the action
    if (action === "approve") {
      const { data: actionLog } = await supabaseServer
        .from("jarvis_action_logs")
        .select("*")
        .eq("id", appr.action_log_id)
        .single();

      if (actionLog) {
        const log = actionLog as any;
        const personaContext: PersonaContext = {
          domain: log.domain,
          task_classification: log.action_type,
        };
        const persona = await selectPersona(userId, personaContext);

        const executionResult = await executeAction(userId, {
          action_type: log.action_type,
          domain: log.domain,
          input: log.input,
        }, persona);

        // Update action log with execution result
        const executionUpdate: Record<string, any> = {
          status: executionResult.success ? "EXECUTED" : "FAILED",
          output: executionResult.output,
          error: executionResult.error,
          executed_at: executionResult.success ? new Date().toISOString() : null,
        };
        await (supabaseServer as any)
          .from("jarvis_action_logs")
          .update(executionUpdate)
          .eq("id", appr.action_log_id);
      }
    }

    return NextResponse.json({ ok: true, status: newStatus });
  } catch (error: any) {
    console.error("Approval error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

