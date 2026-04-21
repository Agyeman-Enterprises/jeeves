import { supabaseServer } from "@/lib/supabase/server";

export interface IdentityProfile {
  user_id: string;
  core_values?: Record<string, any>;
  behavioral_guidelines?: Record<string, any>;
  communication_priorities?: Record<string, any>;
  safety_rules?: Record<string, any>;
  alignment_preferences?: Record<string, any>;
  dislikes?: string[];
  red_lines?: string[];
  priority_domains?: string[];
  personality_calibration?: Record<string, any>;
  relational_patterns?: Record<string, any>;
}

export async function getIdentityProfile(userId: string): Promise<IdentityProfile | null> {
  const { data } = await supabaseServer
    .from("jarvis_identity_profile")
    .select("*")
    .eq("user_id", userId)
    .single();

  if (!data) {
    // Return default identity profile
    return {
      user_id: userId,
      core_values: {
        patient_safety: "highest_priority",
        clinical_excellence: "essential",
        operational_efficiency: "important",
        financial_prudence: "important",
      },
      behavioral_guidelines: {
        always_escalate_critical_clinical: true,
        respect_privacy: true,
        maintain_professional_boundaries: true,
      },
      communication_priorities: {
        clarity: "high",
        brevity: "medium",
        empathy: "context_dependent",
      },
      safety_rules: {
        never_auto_approve_controlled_substances: true,
        always_verify_high_risk_actions: true,
      },
      priority_domains: ["clinical", "financial", "operational"],
    };
  }

  return data as IdentityProfile;
}

export async function updateIdentityProfile(
  userId: string,
  updates: Partial<IdentityProfile>
): Promise<void> {
  await supabaseServer
    .from("jarvis_identity_profile")
    .upsert({
      user_id: userId,
      ...updates,
      updated_at: new Date().toISOString(),
    } as any, {
      onConflict: "user_id",
    });
}

