import { NextRequest, NextResponse } from "next/server";
import {
  activateKillSwitch,
  deactivateKillSwitch,
  getActiveKillSwitches,
  freezeAgent,
  freezeDomain,
  freezeAutomation,
  fullShutdown,
  resumeAgent,
  resumeDomain,
  resumeAutomation,
  resumeAll,
} from "@/lib/jarvis/governance/killswitch";
import type { KillSwitchType } from "@/lib/jarvis/governance/types";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { action, switch_type, target, reason, expires_at } = body;
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    if (action === "activate") {
      if (!switch_type || !target) {
        return NextResponse.json(
          { error: "Missing switch_type or target" },
          { status: 400 }
        );
      }

      const id = await activateKillSwitch(
        userId,
        switch_type as KillSwitchType,
        target,
        reason,
        expires_at
      );

      return NextResponse.json({ ok: true, id, message: "Kill switch activated" });
    }

    if (action === "deactivate") {
      if (!switch_type || !target) {
        return NextResponse.json(
          { error: "Missing switch_type or target" },
          { status: 400 }
        );
      }

      await deactivateKillSwitch(userId, switch_type as KillSwitchType, target);

      return NextResponse.json({ ok: true, message: "Kill switch deactivated" });
    }

    // Convenience actions
    if (action === "freeze_agent") {
      if (!target) {
        return NextResponse.json({ error: "Missing agent slug" }, { status: 400 });
      }
      const id = await freezeAgent(userId, target, reason);
      return NextResponse.json({ ok: true, id, message: `Agent ${target} frozen` });
    }

    if (action === "freeze_domain") {
      if (!target) {
        return NextResponse.json({ error: "Missing domain" }, { status: 400 });
      }
      const id = await freezeDomain(userId, target, reason);
      return NextResponse.json({ ok: true, id, message: `Domain ${target} frozen` });
    }

    if (action === "freeze_automation") {
      const id = await freezeAutomation(userId, reason);
      return NextResponse.json({ ok: true, id, message: "Automation frozen" });
    }

    if (action === "full_shutdown") {
      const id = await fullShutdown(userId, reason);
      return NextResponse.json({ ok: true, id, message: "Full shutdown activated" });
    }

    if (action === "resume_agent") {
      if (!target) {
        return NextResponse.json({ error: "Missing agent slug" }, { status: 400 });
      }
      await resumeAgent(userId, target);
      return NextResponse.json({ ok: true, message: `Agent ${target} resumed` });
    }

    if (action === "resume_domain") {
      if (!target) {
        return NextResponse.json({ error: "Missing domain" }, { status: 400 });
      }
      await resumeDomain(userId, target);
      return NextResponse.json({ ok: true, message: `Domain ${target} resumed` });
    }

    if (action === "resume_automation") {
      await resumeAutomation(userId);
      return NextResponse.json({ ok: true, message: "Automation resumed" });
    }

    if (action === "resume_all") {
      await resumeAll(userId);
      return NextResponse.json({ ok: true, message: "All kill switches deactivated" });
    }

    return NextResponse.json(
      { error: "Invalid action. Use: activate, deactivate, freeze_agent, freeze_domain, freeze_automation, full_shutdown, resume_agent, resume_domain, resume_automation, resume_all" },
      { status: 400 }
    );
  } catch (error: any) {
    console.error("Kill switch error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const activeSwitches = await getActiveKillSwitches(userId);

    return NextResponse.json({ switches: activeSwitches });
  } catch (error: any) {
    console.error("Get kill switches error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

