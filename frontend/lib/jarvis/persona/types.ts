export type PersonaSlug =
  | "executive_ceo"
  | "clinical_professional"
  | "technical_cto"
  | "financial_analyst"
  | "creative_narrative"
  | "inner_circle";

export type Verbosity = "low" | "medium" | "high";
export type Formality = "low" | "medium" | "high";
export type RiskLevel = "strict" | "moderate" | "flexible";
export type EmpathyLevel = "none" | "low" | "medium" | "high";

export interface PersonaProfile {
  id?: string;
  slug: PersonaSlug;
  name: string;
  description?: string;
  tone: string;
  verbosity: Verbosity;
  formality: Formality;
  legal_sensitivity: boolean;
  risk_level: RiskLevel;
  sentence_structure: string;
  domain_rules?: Record<string, any>;
  vocabulary_constraints?: Record<string, any>;
  empathy_level: EmpathyLevel;
}

export interface PersonaContext {
  task_classification?: string;
  recipient_role?: string;
  domain?: "clinical" | "financial" | "technical" | "creative" | "executive" | "personal" | "ops" | "email" | "calendar" | "files";
  urgency?: "low" | "medium" | "high" | "critical";
  communication_channel?: "email" | "note" | "internal" | "patient_app" | "slack" | "direct";
  is_patient_interaction?: boolean;
  is_internal_team?: boolean;
  is_technical_task?: boolean;
  is_creative_task?: boolean;
  is_direct_to_user?: boolean;
}

export interface PersonaSelection {
  persona: PersonaProfile;
  reasoning: string;
  tone_adjustments?: Record<string, any>;
}

