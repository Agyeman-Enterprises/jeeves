export const env = {
  baseURL: process.env.E2E_URL || "http://localhost:3002",
  // JARVIS is a personal local tool — no authentication required
  routes: {
    home: "/jarvis/home",
    jarvis: "/jarvis",
    console: "/jarvis/console",
    finance: "/finance",
    adai: "/adai",
    nexus: "/nexus",
    creative: "/creative",
    playground: "/playground",
    projects: "/projects",
  },
}
