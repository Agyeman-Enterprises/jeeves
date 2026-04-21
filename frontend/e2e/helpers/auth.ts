import { Page } from "@playwright/test"
import { env } from "../env"

// JARVIS is a personal local tool — no auth required.
// This helper navigates to the home page.
export async function goHome(page: Page) {
  await page.goto(env.routes.home)
  await page.waitForLoadState("networkidle")
}
