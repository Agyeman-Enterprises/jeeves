import { test, expect } from "@playwright/test"
import { env } from "../env"

test("app loads from root", async ({ page }) => {
  await page.goto(env.baseURL)
  await expect(page).toHaveTitle(/.+/)
})

test("root redirects to /jarvis/home", async ({ page }) => {
  await page.goto(env.baseURL)
  await expect(page).toHaveURL(/\/jarvis\/home/, { timeout: 10000 })
})

test("home page renders content", async ({ page }) => {
  await page.goto(env.routes.home)
  await page.waitForLoadState("networkidle")
  const body = await page.textContent("body")
  expect(body?.length).toBeGreaterThan(50)
})

test("page does not show application crash error", async ({ page }) => {
  await page.goto(env.routes.home)
  const body = await page.textContent("body")
  expect(body).not.toMatch(/Application error|unhandled|ChunkLoadError/i)
})
