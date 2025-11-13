import { defineConfig, devices } from "@playwright/test"

export default defineConfig({
    testDir: "./tests/e2e",
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: "html",

    use: {
        baseURL: "http://localhost:5173",
        trace: "on-first-retry",
        headless: !!process.env.CI, // Headless in CI, headed locally for debugging
        launchOptions: {
            timeout: 60000, // 60 seconds timeout for browser launch
        },
    },

    projects: process.env.CI
        ? [
              // CI/CD: Only Chromium for reliability
              {
                  name: "chromium",
                  use: {
                      ...devices["Desktop Chrome"],
                  },
              },
          ]
        : [
              // Local development: All browsers with extended timeouts
              {
                  name: "chromium",
                  use: {
                      ...devices["Desktop Chrome"],
                  },
              },
              {
                  name: "firefox",
                  use: {
                      ...devices["Desktop Firefox"],
                      launchOptions: {
                          timeout: 180000, // 3 minutes for Firefox in local dev
                          args: ["--no-sandbox", "--disable-setuid-sandbox"],
                      },
                  },
              },
              {
                  name: "webkit",
                  use: {
                      ...devices["Desktop Safari"],
                      launchOptions: {
                          timeout: 180000, // 3 minutes for WebKit in local dev
                      },
                  },
              },
          ],

    webServer: {
        command: "npm run dev",
        url: "http://localhost:5173",
        reuseExistingServer: !process.env.CI,
    },
})
