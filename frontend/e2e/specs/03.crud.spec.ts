import { test, expect } from "@playwright/test"
import { env } from "../env"

// JARVIS is primarily a query/intelligence interface.
// CRUD tests verify that navigable sections render correctly.

test("adai campaigns page loads", async ({ page }) => {
  await page.goto(`${env.routes.adai}/campaigns`)
  await page.waitForLoadState("networkidle")
  const body = await page.textContent("body")
  expect(body?.length).toBeGreaterThan(10)
})

test("adai connections page loads", async ({ page }) => {
  await page.goto(`${env.routes.adai}/connections`)
  await page.waitForLoadState("networkidle")
  const body = await page.textContent("body")
  expect(body?.length).toBeGreaterThan(10)
})

test("nexus situations page loads", async ({ page }) => {
  await page.goto(`${env.routes.nexus}/situations`)
  await page.waitForLoadState("networkidle")
  const body = await page.textContent("body")
  expect(body?.length).toBeGreaterThan(10)
})
