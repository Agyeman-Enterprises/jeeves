import { test, expect } from "@playwright/test"
import { env } from "../env"

// JARVIS is a personal local tool with no authentication.
// These tests verify all routes are publicly accessible.

test("home page loads without auth", async ({ page }) => {
  await page.goto(env.routes.home)
  await expect(page).not.toHaveURL(/login/)
})

test("finance page loads without auth", async ({ page }) => {
  await page.goto(env.routes.finance)
  await page.waitForLoadState("networkidle")
  await expect(page).not.toHaveURL(/login/)
})

test("nexus page loads without auth", async ({ page }) => {
  await page.goto(env.routes.nexus)
  await page.waitForLoadState("networkidle")
  await expect(page).not.toHaveURL(/login/)
})

test("adai page loads without auth", async ({ page }) => {
  await page.goto(env.routes.adai)
  await page.waitForLoadState("networkidle")
  await expect(page).not.toHaveURL(/login/)
})
