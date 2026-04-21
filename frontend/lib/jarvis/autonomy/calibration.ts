import { supabaseServer } from "@/lib/supabase/server";
import type { AutonomyMode, AutonomyCalibration, CalibrationType } from "./types";
import { getDomainAutonomy, setDomainAutonomyMode } from "./modes";
import { logAutonomyChange } from "./history";

export async function calibrateAutonomy(
  userId: string,
  domain: string,
  behaviorEvidence: Record<string, any>
): Promise<AutonomyCalibration | null> {
  // Check if auto-calibration is enabled
  const { data: settings } = await supabaseServer
    .from("jarvis_autonomy_settings")
    .select("auto_calibration_enabled")
    .eq("user_id", userId)
    .single();

  if (!settings || !(settings as any).auto_calibration_enabled) {
    return null; // Auto-calibration disabled
  }

  const domainAutonomy = await getDomainAutonomy(userId, domain);
  if (!domainAutonomy) {
    return null;
  }

  // Analyze behavior evidence
  const approvalRate = behaviorEvidence.approval_rate || 0;
  const modificationRate = behaviorEvidence.modification_rate || 0;
  const rejectionRate = behaviorEvidence.rejection_rate || 0;

  // Determine calibration type
  let calibrationType: CalibrationType = "MAINTAIN";
  let newMode: AutonomyMode | undefined;

  // If user consistently approves (>80%), consider increasing autonomy
  if (approvalRate > 0.8 && domainAutonomy.current_mode !== "AUTONOMOUS") {
    const allowedModes = domainAutonomy.allowed_modes;
    const currentIndex = allowedModes.indexOf(domainAutonomy.current_mode);
    
    if (currentIndex < allowedModes.length - 1) {
      const nextMode = allowedModes[currentIndex + 1];
      if (nextMode) {
        calibrationType = "INCREASE";
        newMode = nextMode;
      }
    }
  }

  // If user consistently rejects or modifies (>50%), consider decreasing autonomy
  if ((rejectionRate > 0.5 || modificationRate > 0.5) && domainAutonomy.current_mode !== "ASSISTIVE") {
    const allowedModes = domainAutonomy.allowed_modes;
    const currentIndex = allowedModes.indexOf(domainAutonomy.current_mode);
    
    if (currentIndex > 0) {
      const prevMode = allowedModes[currentIndex - 1];
      if (prevMode) {
        calibrationType = "DECREASE";
        newMode = prevMode;
      }
    }
  }

  // Calculate confidence score
  const confidenceScore = Math.min(approvalRate, 1 - rejectionRate);

  // Create calibration record
  const { data: calibration } = await supabaseServer
    .from("jarvis_autonomy_calibration")
    .insert({
      user_id: userId,
      domain,
      calibration_type: calibrationType,
      previous_mode: domainAutonomy.current_mode,
      new_mode: newMode,
      behavior_evidence: behaviorEvidence,
      confidence_score: confidenceScore,
      applied: false,
    } as any)
    .select()
    .single();

  // Apply calibration if confidence is high enough
  if (calibration && newMode && confidenceScore > 0.7) {
    await setDomainAutonomyMode(userId, domain, newMode);
    await logAutonomyChange(userId, {
      domain,
      previous_mode: domainAutonomy.current_mode,
      new_mode: newMode,
      reason: `Auto-calibration: ${calibrationType} based on behavior patterns`,
      triggered_by: "behavior",
      confidence_score: confidenceScore,
    });

    // Mark calibration as applied
    await (supabaseServer as any)
      .from("jarvis_autonomy_calibration")
      .update({ applied: true } as any)
      .eq("id", (calibration as any).id);
  }

  return calibration as AutonomyCalibration;
}

export async function getBehaviorScore(userId: string): Promise<number> {
  // Calculate behavior score based on recent interactions
  // This is a simplified version - in production, use more sophisticated analysis

  const { data: recentActions } = await supabaseServer
    .from("jarvis_action_logs")
    .select("status, output")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(100);

  if (!recentActions || recentActions.length === 0) {
    return 0.5; // Default score
  }

  const actions = recentActions as Array<{ status: string; output?: any }>;
  const approved = actions.filter((a) => a.status === "EXECUTED" || a.status === "APPROVED").length;
  const rejected = actions.filter((a) => a.status === "REJECTED").length;
  const total = recentActions.length;

  const approvalRate = approved / total;
  const rejectionRate = rejected / total;

  // Behavior score is based on approval rate minus rejection rate
  const behaviorScore = Math.max(0, Math.min(1, approvalRate - rejectionRate * 0.5));

  // Update global settings
  await (supabaseServer as any)
    .from("jarvis_autonomy_settings")
    .update({ behavior_score: behaviorScore } as any)
    .eq("user_id", userId);

  return behaviorScore;
}

