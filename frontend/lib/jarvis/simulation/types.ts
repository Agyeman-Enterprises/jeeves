export type SimulationType = "CLINICAL" | "FINANCIAL" | "OPERATIONAL" | "RISK" | "AGENT" | "STRATEGIC";
export type TimeHorizon = "1WEEK" | "1MONTH" | "3MONTHS" | "6MONTHS" | "1YEAR";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type StrategyType = "CONSERVATIVE" | "BALANCED" | "AGGRESSIVE" | "EXPANSION" | "CASHFLOW_PRESERVATION";
export type RiskType = "CLINICAL" | "FINANCIAL" | "OPERATIONAL" | "LEGAL" | "COMPLIANCE" | "REPUTATION";

export interface Simulation {
  id?: string;
  user_id: string;
  simulation_type: SimulationType;
  simulation_name: string;
  scenario_description?: string;
  input_parameters: Record<string, any>;
  output_results?: Record<string, any>;
  status?: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
  started_at?: string;
  completed_at?: string;
  created_at?: string;
}

export interface SimulationScenario {
  id?: string;
  user_id: string;
  scenario_name: string;
  scenario_type: SimulationType;
  description?: string;
  parameters: Record<string, any>;
  expected_outcomes?: Record<string, any>;
  is_template?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ClinicalPrediction {
  id?: string;
  user_id: string;
  patient_id?: string;
  prediction_type: "GLP_PROGRESSION" | "FOLLOWUP_NEED" | "LAB_TREND" | "HOSPITALIZATION_RISK" | "CLINIC_LOAD";
  time_horizon: TimeHorizon;
  predicted_value: Record<string, any>;
  confidence_score?: number;
  factors?: Record<string, any>;
  created_at?: string;
  expires_at?: string;
}

export interface FinancialPrediction {
  id?: string;
  user_id: string;
  entity_id?: string;
  prediction_type: "CASHFLOW" | "REVENUE" | "TAX_LIABILITY" | "PROFITABILITY";
  time_horizon: TimeHorizon;
  predicted_value: Record<string, any>; // Time series data
  confidence_score?: number;
  assumptions?: Record<string, any>;
  sensitivity_analysis?: Record<string, any>;
  created_at?: string;
  expires_at?: string;
}

export interface OperationalPrediction {
  id?: string;
  user_id: string;
  prediction_type: "SCHEDULING_BOTTLENECK" | "MA_WORKLOAD" | "CHARTING_BACKLOG" | "APPOINTMENT_DEMAND";
  time_horizon: TimeHorizon;
  predicted_value: Record<string, any>;
  confidence_score?: number;
  risk_level?: RiskLevel;
  recommendations?: Record<string, any>;
  created_at?: string;
  expires_at?: string;
}

export interface RiskPrediction {
  id?: string;
  user_id: string;
  risk_type: RiskType;
  risk_category: string;
  severity: RiskLevel;
  probability?: number;
  impact?: Record<string, any>;
  time_horizon?: TimeHorizon;
  mitigation_strategies?: Record<string, any>;
  created_at?: string;
  expires_at?: string;
}

export interface AgentLoadPrediction {
  id?: string;
  user_id: string;
  agent_slug: string;
  time_horizon: TimeHorizon;
  predicted_load: Record<string, any>;
  overload_probability?: number;
  recommendations?: Record<string, any>;
  created_at?: string;
  expires_at?: string;
}

export interface StrategicScenario {
  id?: string;
  user_id: string;
  scenario_name: string;
  goal: string;
  strategy_type?: StrategyType;
  timeline?: Record<string, any>;
  required_resources?: Record<string, any>;
  projected_outcomes?: Record<string, any>;
  risk_map?: Record<string, any>;
  financial_sensitivity?: Record<string, any>;
  operational_constraints?: Record<string, any>;
  recommended_path?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface SimulationModel {
  id?: string;
  user_id: string;
  model_type: SimulationType;
  model_name: string;
  model_config: Record<string, any>;
  training_data_range?: Record<string, any>;
  accuracy_metrics?: Record<string, any>;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

