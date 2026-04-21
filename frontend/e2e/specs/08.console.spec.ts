import { test, expect } from "@playwright/test"
import { env } from "../env"

test("no uncaught JS errors on home load", async ({ page }) => {
  const errors: string[] = []
  page.on("pageerror", (err) => errors.push(err.message))
  await page.goto(env.routes.home)
  await page.waitForLoadState("networkidle")
  expect(errors).toEqual([])
})

test("no failed network requests on home load", async ({ page }) => {
  const failed: string[] = []
  page.on("requestfailed", (req) => {
    const url = req.url()
    // Ignore WebSocket HMR connections in dev mode
    if (!url.startsWith("ws://") && !url.includes("_next/webpack-hmr")) {
      failed.push(`${req.method()} ${url}`)
    }
  })
  await page.goto(env.routes.home)
  await page.waitForLoadState("networkidle")
  expect(failed).toEqual([])
})

test("no 500 responses on any primary page", async ({ page }) => {
  const serverErrors: string[] = []
  page.on("response", (res) => {
    if (res.status() >= 500) {
      serverErrors.push(`${res.status()} ${res.url()}`)
    }
  })
  await page.goto(env.routes.home)
  await page.waitForLoadState("networkidle")
  expect(serverErrors).toEqual([])
})
