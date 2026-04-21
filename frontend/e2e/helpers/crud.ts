import { Page, expect } from "@playwright/test"

// JARVIS is a read/query interface — no user-facing CRUD forms
// Helpers verify that sections render correctly

export async function assertSectionLoads(page: Page, route: string) {
  await page.goto(route)
  await page.waitForLoadState("networkidle")
  const body = await page.textContent("body")
  expect(body?.length).toBeGreaterThan(50)
}
