import { test, expect } from "@playwright/test"
import { env } from "../env"

test("jarvis home renders", async ({ page }) => {
  await page.goto(env.routes.home)
  await page.waitForLoadState("networkidle")
  const body = await page.textContent("body")
  expect(body?.length).toBeGreaterThan(50)
})

test("jarvis console page loads", async ({ page }) => {
  await page.goto(env.routes.console)
  await page.waitForLoadState("networkidle")
  await expect(page).not.toHaveURL(/404/)
})

test("playground page loads", async ({ page }) => {
  await page.goto(env.routes.playground)
  await page.waitForLoadState("networkidle")
  await expect(page).not.toHaveURL(/404/)
})

test("creative page loads", async ({ page }) => {
  await page.goto(env.routes.creative)
  await page.waitForLoadState("networkidle")
  await expect(page).not.toHaveURL(/404/)
})

test("finance page renders content", async ({ page }) => {
  await page.goto(env.routes.finance)
  await page.waitForLoadState("networkidle")
  const body = await page.textContent("body")
  expect(body?.length).toBeGreaterThan(50)
})
