import { test, expect } from "@playwright/test"
import { env } from "../env"

// JARVIS has no role-based permissions — all routes are open.
// These tests ensure no route accidentally enforces auth.

const publicRoutes = [
  "/jarvis/home",
  "/finance",
  "/adai",
  "/nexus",
  "/creative",
  "/playground",
]

for (const route of publicRoutes) {
  test(`${route} is accessible without credentials`, async ({ page }) => {
    await page.goto(`${env.baseURL}${route}`)
    await page.waitForLoadState("networkidle")
    await expect(page).not.toHaveURL(/login/)
    // Should not be a blank page
    const body = await page.textContent("body")
    expect(body?.length).toBeGreaterThan(10)
  })
}
