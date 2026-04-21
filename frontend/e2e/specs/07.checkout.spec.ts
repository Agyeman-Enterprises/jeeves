import { test, expect } from "@playwright/test"
import { env } from "../env"

// JARVIS has no billing — verify no billing-related 500s
test("no billing route crashes the app", async ({ page }) => {
  // JARVIS doesn't have a /checkout route — navigating to root shouldn't crash
  await page.goto(env.baseURL)
  await expect(page).toHaveTitle(/.+/)
  const body = await page.textContent("body")
  expect(body).not.toMatch(/Application error/i)
})
