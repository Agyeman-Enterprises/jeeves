import type { RefactoringLevel } from "./types";

export interface SafetyCheck {
  allowed: boolean;
  reason?: string;
  constraints?: string[];
}

export async function checkSafetyConstraints(
  userId: string,
  level: RefactoringLevel,
  targetComponent: string
): Promise<SafetyCheck> {
  // Safety rules based on refactoring level
  const constraints: string[] = [];

  // Level 1 (PARAMETRIC) - Always allowed
  if (level === "PARAMETRIC") {
    return { allowed: true, constraints: [] };
  }

  // Level 2 (STRUCTURAL) - Check for critical components
  if (level === "STRUCTURAL") {
    const criticalComponents = ["RLS", "AUTH", "CLINICAL_SAFETY", "FINANCIAL_PERMISSIONS"];
    if (criticalComponents.some((c) => targetComponent.includes(c))) {
      return {
        allowed: false,
        reason: "Cannot modify critical safety components",
        constraints: ["Cannot change RLS", "Cannot modify clinical safety rules"],
      };
    }
  }

  // Level 3 (MODULAR) - Check for external permissions
  if (level === "MODULAR") {
    if (targetComponent.includes("EXTERNAL_API") || targetComponent.includes("PERMISSIONS")) {
      return {
        allowed: false,
        reason: "Cannot create agents with external authority without approval",
        constraints: ["Cannot expand external permissions"],
      };
    }
  }

  // Level 4 (FULL_BRAIN_SCHEMA) - Most restrictive
  if (level === "FULL_BRAIN_SCHEMA") {
    const forbiddenComponents = [
      "RLS",
      "AUTH",
      "CLINICAL_SAFETY",
      "FINANCIAL_PERMISSIONS",
      "KILL_SWITCH",
      "AUDIT_LOG",
    ];

    if (forbiddenComponents.some((c) => targetComponent.includes(c))) {
      return {
        allowed: false,
        reason: "Cannot modify critical governance components",
        constraints: [
          "Cannot change RLS",
          "Cannot alter clinical safety rules",
          "Cannot modify financial permissions",
          "Cannot change kill-switch system",
          "Cannot modify audit logs",
        ],
      };
    }
  }

  return { allowed: true, constraints };
}

export function canAutoImplement(level: RefactoringLevel): boolean {
  // Only PARAMETRIC and some STRUCTURAL changes can be auto-implemented
  return level === "PARAMETRIC" || level === "STRUCTURAL";
}

export function requiresUserApproval(level: RefactoringLevel): boolean {
  // MODULAR and FULL_BRAIN_SCHEMA always require approval
  return level === "MODULAR" || level === "FULL_BRAIN_SCHEMA";
}

