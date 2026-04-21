import type {
  JarvisCommandInput,
  JarvisTaskClassification,
} from "../types";
import { classifyTaskWithLLM } from "./llm";
import { applyWorkspaceBias } from "../context/workspaceBias";

interface ClassifyArgs extends JarvisCommandInput {}

function ruleBasedClassify(query: string): JarvisTaskClassification {
  const lower = query.toLowerCase();

  if (
    lower.includes("schedule") ||
    lower.includes("calendar") ||
    lower.includes("book") ||
    lower.includes("appointment")
  ) {
    return {
      kind: "SCHEDULE",
      confidence: 0.8,
      reason: "Rule-based: scheduling language detected.",
      tags: ["calendar", "time"],
    };
  }

  if (
    lower.includes("email") ||
    lower.includes("inbox") ||
    lower.includes("reply")
  ) {
    return {
      kind: "EMAIL",
      confidence: 0.75,
      reason: "Rule-based: email-related language detected.",
      tags: ["email"],
    };
  }

  if (lower.includes("file") || lower.includes("document")) {
    return {
      kind: "FILE_OP",
      confidence: 0.7,
      reason: "Rule-based: file/document language detected.",
      tags: ["files"],
    };
  }

  if (
    lower.includes("analytics") ||
    lower.includes("dashboard") ||
    lower.includes("metrics")
  ) {
    return {
      kind: "ANALYTICS",
      confidence: 0.7,
      reason: "Rule-based: analytics/dashboard language detected.",
      tags: ["analytics"],
    };
  }

  return {
    kind: "QUESTION",
    confidence: 0.6,
    reason: "Rule-based: defaulted to QUESTION.",
    tags: [],
  };
}

export async function classifyTask(
  args: ClassifyArgs
): Promise<JarvisTaskClassification> {
  const { query } = args;

  const ruleBased = ruleBasedClassify(query);

  // Try LLM. If unavailable or fails, stick to rule-based.
  try {
    const llmClassification = await classifyTaskWithLLM({
      ...args,
      ruleBased,
    });

    if (!llmClassification) {
      // Apply workspace-aware bias to rule-based
      return applyWorkspaceBias(ruleBased, args);
    }

    // Optional: blend confidences or prefer the higher one.
    let chosen: JarvisTaskClassification;
    if (llmClassification.confidence >= ruleBased.confidence) {
      chosen = {
        ...llmClassification,
        reason: `LLM: ${llmClassification.reason} (rule-based: ${ruleBased.kind})`,
      };
    } else {
      chosen = ruleBased;
    }

    // Apply workspace-aware bias
    return applyWorkspaceBias(chosen, args);
  } catch (error) {
    console.error("classifyTask LLM error:", error);
    // Apply workspace-aware bias to rule-based fallback
    return applyWorkspaceBias(ruleBased, args);
  }
}

