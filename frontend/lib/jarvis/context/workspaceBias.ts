import type {
  JarvisTaskClassification,
  JarvisCommandInput,
} from "../types";

export function applyWorkspaceBias(
  base: JarvisTaskClassification,
  input: JarvisCommandInput
): JarvisTaskClassification {
  const ctx = input.workspaceContext;
  if (!ctx) return base;

  let classification = { ...base };

  if (ctx.app === "nexus") {
    if (ctx.location === "analytics") {
      if (classification.kind === "QUESTION") {
        classification = {
          ...classification,
          kind: "ANALYTICS",
          confidence: Math.max(classification.confidence, 0.8),
          reason:
            classification.reason +
            " | Workspace bias: user is on Nexus analytics.",
          tags: [...new Set([...classification.tags, "analytics"])],
        };
      }
    }

    if (ctx.location === "email") {
      if (classification.kind === "QUESTION") {
        classification = {
          ...classification,
          kind: "EMAIL",
          confidence: Math.max(classification.confidence, 0.8),
          reason:
            classification.reason +
            " | Workspace bias: user is on Nexus email.",
          tags: [...new Set([...classification.tags, "email"])],
        };
      }
    }

    if (ctx.location === "files") {
      if (classification.kind === "QUESTION") {
        classification = {
          ...classification,
          kind: "FILE_OP",
          confidence: Math.max(classification.confidence, 0.8),
          reason:
            classification.reason +
            " | Workspace bias: user is on Nexus files.",
          tags: [...new Set([...classification.tags, "files"])],
        };
      }
    }
  }

  return classification;
}

