import { test, expect } from "@playwright/test"
import { env } from "../env"

// JARVIS has no session/auth — tests verify navigation state persists

test("page state survives reload on home", async ({ page }) => {
  await page.goto(env.routes.home)
  await page.waitForLoadState("networkidle")
  await page.reload()
  await expect(page).toHaveURL(/\/jarvis\/home/)
})

test("page state survives reload on finance", async ({ page }) => {
  await page.goto(env.routes.finance)
  await page.waitForLoadState("networkidle")
  await page.reload()
  await expect(page).not.toHaveURL(/404/)
})
