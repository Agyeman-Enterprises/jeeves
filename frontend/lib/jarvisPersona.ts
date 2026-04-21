// lib/jarvisPersona.ts

export type JarvisMood =
  | "focused"
  | "playful"
  | "chill"
  | "strategic"
  | "supportive";

export function getGreetingForTime(date: Date, name = "Doctor") {
  const hour = date.getHours();

  if (hour < 5) return `Burning the midnight oil, ${name}?`;
  if (hour < 12) return `Good morning, ${name}. Let's set the tone for the day.`;
  if (hour < 17) return `Good afternoon, ${name}. Ready for the next move?`;
  if (hour < 22) return `Good evening, ${name}. Let's tidy up the day.`;
  return `Late session, ${name}. I've got your back.`;
}

export function getMoodForTime(date: Date): JarvisMood {
  const hour = date.getHours();

  if (hour < 6) return "supportive";
  if (hour < 11) return "focused";
  if (hour < 16) return "strategic";
  if (hour < 20) return "playful";
  return "chill";
}

export function describeMood(mood: JarvisMood) {
  switch (mood) {
    case "focused":
      return "dialed in and ready to execute.";
    case "playful":
      return "in a light mood, but still deadly efficient.";
    case "chill":
      return "calm, steady, and unbothered.";
    case "strategic":
      return "thinking three moves ahead.";
    case "supportive":
      return "here to make sure you don't carry this alone.";
  }
}

