export type DecisionType = "APPROVE" | "DECLINE" | "REVISE" | "IGNORE" | "ESCALATE" | "DELEGATE";
export type ContextType = "CLINICAL" | "FINANCIAL" | "OPERATIONAL" | "COMMUNICATION" | "PERSONAL";
export type ModelType = "CSM" | "CDM" | "OPM" | "FBM" | "PPM";
export type RuleType = "NOTIFICATION" | "AUTOMATION" | "PRIORITY" | "ESCALATION" | "DELEGATION";
export type PatternType = "SCHEDULING" | "TRIAGE" | "CATEGORIZATION" | "RESPONSE_TIME" | "COMMUNICATION_STYLE" | "CLINICAL_REASONING";

export interface BehaviorVector {
  communication?: Record<string, any>;
  clinical?: Record<string, any>;
  operational?: Record<string, any>;
  financial?: Record<string, any>;
  personal?: Record<string, any>;
}

export interface DecisionLog {
  id?: string;
  user_id: string;
  decision_type: DecisionType;
  context_type: ContextType;
  context_id?: string;
  original_input?: Record<string, any>;
  user_action?: Record<string, any>;
  user_feedback?: string;
  model_affected?: ModelType[];
  created_at?: string;
}

export interface CommunicationExample {
  id?: string;
  user_id: string;
  example_type: "EMAIL" | "PATIENT_MESSAGE" | "NOTE" | "SUMMARY";
  original_text?: string;
  revised_text?: string;
  style_notes?: Record<string, any>;
  created_at?: string;
}

export interface PreferenceRule {
  id?: string;
  user_id: string;
  rule_type: RuleType;
  trigger_condition: Record<string, any>;
  action: string;
  confidence?: number;
  source?: "EXPLICIT" | "IMPLICIT" | "INFERRED";
  created_at?: string;
  updated_at?: string;
}

export interface BehaviorPattern {
  id?: string;
  user_id: string;
  pattern_type: PatternType;
  pattern_data: Record<string, any>;
  frequency?: number;
  confidence?: number;
  created_at?: string;
  updated_at?: string;
}

