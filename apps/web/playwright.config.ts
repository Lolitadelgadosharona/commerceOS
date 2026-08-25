import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e",
  use: { baseURL: "http://127.0.0.1:3000" },
  webServer: [
    { command: "node tests/fixtures/executive-api.mjs", port: 4100, reuseExistingServer: !process.env.CI },
    {
      command: "API_INTERNAL_URL=http://127.0.0.1:4100 COMMERCE_OS_API_TOKEN=test-dashboard-token COMMERCE_OS_ORGANIZATION_ID=11111111-1111-4111-8111-111111111111 npm run dev",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
    },
  ],
});
