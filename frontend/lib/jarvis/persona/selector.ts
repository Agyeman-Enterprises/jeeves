import { supabaseServer } from "@/lib/supabase/server";
import type { PersonaContext, PersonaSelection, PersonaProfile, PersonaSlug } from "./types";

export async function selectPersona(
  userId: string,
  context: PersonaContext
): Promise<PersonaSelection> {
  // Get user's persona rules (custom rules take priority)
  const { data: rules } = await supabaseServer
    .from("jarvis_persona_rules")
    .select("*")
    .eq("user_id", userId)
    .order("priority", { ascending: false });

  // Check custom rules first
  if (rules && rules.length > 0) {
    for (const rule of rules) {
      const r = rule as any;
      if (matchesCondition(r.trigger_condition, context)) {
        const persona = await getPersonaBySlug(r.persona_slug);
        if (persona) {
          return {
            persona,
            reasoning: `Matched custom rule: ${r.trigger_condition}`,
          };
        }
      }
    }
  }

  // Apply default selection logic
  let selectedSlug: PersonaSlug = "inner_circle"; // Default

  // Direct to user
  if (context.is_direct_to_user) {
    selectedSlug = "inner_circle";
  }
  // Patient interaction
  else if (context.is_patient_interaction || context.recipient_role === "patient") {
    selectedSlug = "clinical_professional";
  }
  // Technical task
  else if (context.is_technical_task || context.domain === "technical") {
    selectedSlug = "technical_cto";
  }
  // Creative task
  else if (context.is_creative_task || context.domain === "creative") {
    selectedSlug = "creative_narrative";
  }
  // Financial domain
  else if (context.domain === "financial") {
    selectedSlug = "financial_analyst";
  }
  // Internal team
  else if (context.is_internal_team || context.communication_channel === "slack" || context.communication_channel === "internal") {
    selectedSlug = "executive_ceo";
  }
  // Clinical domain (non-patient)
  else if (context.domain === "clinical") {
    selectedSlug = "clinical_professional";
  }
  // Executive/operational
  else if (context.domain === "executive" || context.task_classification === "OPERATIONAL") {
    selectedSlug = "executive_ceo";
  }

  const persona = await getPersonaBySlug(selectedSlug);
  if (!persona) {
    throw new Error(`Persona not found: ${selectedSlug}`);
  }

  // Apply emotional intelligence adjustments
  const toneAdjustments = await getEmotionalAdjustments(userId);

  return {
    persona,
    reasoning: `Selected based on context: ${context.domain || "default"}`,
    tone_adjustments: toneAdjustments,
  };
}

async function getPersonaBySlug(slug: PersonaSlug): Promise<PersonaProfile | null> {
  const { data } = await supabaseServer
    .from("jarvis_personas")
    .select("*")
    .eq("slug", slug)
    .single();

  if (!data) return null;

  return {
    id: (data as any).id,
    slug: (data as any).slug,
    name: (data as any).name,
    description: (data as any).description,
    tone: (data as any).tone,
    verbosity: (data as any).verbosity,
    formality: (data as any).formality,
    legal_sensitivity: (data as any).legal_sensitivity,
    risk_level: (data as any).risk_level,
    sentence_structure: (data as any).sentence_structure,
    domain_rules: (data as any).domain_rules,
    vocabulary_constraints: (data as any).vocabulary_constraints,
    empathy_level: (data as any).empathy_level,
  };
}

async function getEmotionalAdjustments(userId: string): Promise<Record<string, any> | undefined> {
  // Check for active emotional context
  const { data: contexts } = await supabaseServer
    .from("jarvis_emotional_context")
    .select("*")
    .eq("user_id", userId)
    .gt("expires_at", new Date().toISOString())
    .order("detected_at", { ascending: false })
    .limit(1);

  if (!contexts || contexts.length === 0) {
    return undefined;
  }

  const context = contexts[0] as any;
  return context.tone_adjustment;
}

function matchesCondition(
  condition: Record<string, any>,
  context: PersonaContext
): boolean {
  for (const [key, value] of Object.entries(condition)) {
    if (context[key as keyof PersonaContext] !== value) {
      return false;
    }
  }
  return true;
}

export async function getPersonaPrompt(persona: PersonaProfile, adjustments?: Record<string, any>): Promise<string> {
  let prompt = `You are operating in ${persona.name} mode.

Tone: ${persona.tone}
Verbosity: ${persona.verbosity}
Formality: ${persona.formality}
Empathy Level: ${persona.empathy_level}
Sentence Structure: ${persona.sentence_structure}
Risk Level: ${persona.risk_level}
${persona.legal_sensitivity ? "Legal Sensitivity: HIGH - Ensure all communications are legally safe and appropriate." : ""}

${persona.description ? `Context: ${persona.description}` : ""}

${persona.domain_rules ? `Domain Rules: ${JSON.stringify(persona.domain_rules)}` : ""}
${persona.vocabulary_constraints ? `Vocabulary: ${JSON.stringify(persona.vocabulary_constraints)}` : ""}`;

  // Apply emotional adjustments
  if (adjustments) {
    if (adjustments.softer) {
      prompt += "\n\nTone Adjustment: Use a softer, more gentle tone. Be more concise and respectful of energy levels.";
    }
    if (adjustments.firmer) {
      prompt += "\n\nTone Adjustment: Use a firmer, clearer tone. Be direct and action-oriented.";
    }
    if (adjustments.encouraging) {
      prompt += "\n\nTone Adjustment: Offer encouragement and support where appropriate.";
    }
  }

  return prompt;
}

