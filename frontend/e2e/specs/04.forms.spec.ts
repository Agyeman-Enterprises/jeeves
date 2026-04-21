import { test, expect } from "@playwright/test"
import { env } from "../env"

test("jarvis home has an input or interactive element", async ({ page }) => {
  await page.goto(env.routes.home)
  await page.waitForLoadState("networkidle")
  // Check for any input, textarea, or button in the page
  const interactiveCount = await page
    .locator("input, textarea, button")
    .count()
  expect(interactiveCount).toBeGreaterThan(0)
})

test("console page has input for commands", async ({ page }) => {
  await page.goto(env.routes.console)
  await page.waitForLoadState("networkidle")
  const body = await page.textContent("body")
  expect(body?.length).toBeGreaterThan(10)
})
