import type { Signal, PrioritizedItem } from "./types";

export function rankSignals(signals: Signal[]): PrioritizedItem[] {
  return signals.map((signal) => {
    const urgency = calculateUrgency(signal);
    const impact = calculateImpact(signal);
    const risk = calculateRisk(signal);
    const reversibility = calculateReversibility(signal);
    const deadline_proximity = calculateDeadlineProximity(signal);

    // Priority score: weighted combination
    const priority_score =
      urgency * 0.3 +
      impact * 0.25 +
      risk * 0.25 +
      (100 - reversibility) * 0.1 +
      (deadline_proximity ? (100 - deadline_proximity) * 0.1 : 0);

    return {
      ...signal,
      urgency,
      impact,
      risk,
      reversibility,
      deadline_proximity,
      priority_score: Math.round(priority_score),
    };
  }).sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0));
}

function calculateUrgency(signal: Signal): number {
  // Severity-based urgency
  const severityMap: Record<string, number> = {
    CRITICAL: 100,
    HIGH: 75,
    MEDIUM: 50,
    LOW: 25,
  };

  let urgency = severityMap[signal.severity] || 50;

  // Type-based adjustments
  if (signal.type === "CLINICAL" && signal.severity === "CRITICAL") {
    urgency = 100; // Critical clinical issues are always urgent
  }

  if (signal.type === "FINANCIAL" && signal.severity === "HIGH") {
    urgency = 85; // High financial issues are very urgent
  }

  return urgency;
}

function calculateImpact(signal: Signal): number {
  // Type-based impact
  const typeMap: Record<string, number> = {
    CLINICAL: 90,
    FINANCIAL: 80,
    OPERATIONAL: 60,
    SYSTEM: 50,
    PERSONAL: 40,
  };

  let impact = typeMap[signal.type] || 50;

  // Severity adjustments
  if (signal.severity === "CRITICAL") {
    impact = Math.min(100, impact + 20);
  } else if (signal.severity === "HIGH") {
    impact = Math.min(100, impact + 10);
  }

  return impact;
}

function calculateRisk(signal: Signal): number {
  // Severity is a proxy for risk
  const severityMap: Record<string, number> = {
    CRITICAL: 100,
    HIGH: 75,
    MEDIUM: 50,
    LOW: 25,
  };

  let risk = severityMap[signal.severity] || 50;

  // Type-based risk adjustments
  if (signal.type === "CLINICAL" && signal.severity === "CRITICAL") {
    risk = 100; // Critical clinical = maximum risk
  }

  if (signal.type === "FINANCIAL" && signal.severity === "HIGH") {
    risk = 85; // High financial = high risk
  }

  return risk;
}

function calculateReversibility(signal: Signal): number {
  // Some issues are more reversible than others
  if (signal.type === "OPERATIONAL" && signal.severity === "LOW") {
    return 80; // Low operational issues are easily reversible
  }

  if (signal.type === "CLINICAL" && signal.severity === "CRITICAL") {
    return 20; // Critical clinical issues are less reversible
  }

  if (signal.type === "FINANCIAL" && signal.severity === "HIGH") {
    return 40; // High financial issues are somewhat reversible
  }

  return 60; // Default moderate reversibility
}

function calculateDeadlineProximity(signal: Signal): number | undefined {
  // Check if signal has deadline information
  const deadline = signal.payload?.deadline || signal.payload?.due_date;
  if (!deadline) return undefined;

  const deadlineDate = new Date(deadline);
  const now = new Date();
  const daysUntil = Math.ceil(
    (deadlineDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  );

  // Return days until deadline (0-100 scale, where 0 = overdue, 100 = far away)
  if (daysUntil < 0) return 0; // Overdue
  if (daysUntil > 30) return 100; // Far away
  return Math.round((daysUntil / 30) * 100);
}

