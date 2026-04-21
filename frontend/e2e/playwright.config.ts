import { defineConfig, devices } from "@playwright/test"
import { fileURLToPath } from "url"
import path from "path"
import { env } from "./env.js"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const nodeExe = "C:\\nvm4w\\nodejs\\node.exe"
const nextBin = path.resolve(__dirname, "../node_modules/next/dist/bin/next")

export default defineConfig({
  testDir: "./specs",
  timeout: 60000,
  retries: process.env.CI ? 2 : 0,
  reporter: [["html"], ["list"]],
  webServer: {
    command: `"${nodeExe}" "${nextBin}" dev -p 3002`,
    cwd: path.resolve(__dirname, ".."),
    port: 3002,
    timeout: 120000,
    reuseExistingServer: true,
  },
  use: {
    baseURL: env.baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
})
