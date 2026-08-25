import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  await request.post("http://127.0.0.1:4100/__scenario/success");
});

test("renders real Executive Dashboard contracts and navigable records", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "Executive dashboard" })).toBeVisible();
  await expect(page.getByText("Observed revenue")).toBeVisible();
  await expect(page.getByText("$12,500")).toBeVisible();
  await expect(page.getByRole("link", { name: /Customer-backed opportunity ready/ })).toHaveAttribute("href", /\/opportunities\?signal=/);
  await expect(page.getByRole("link", { name: /Review contribution margin risk/ })).toHaveAttribute("href", /\/decisions\?item=/);
});

test("renders intentional empty states without fabricated values", async ({ page, request }) => {
  await request.post("http://127.0.0.1:4100/__scenario/empty");
  await page.goto("/dashboard");
  await expect(page.getByText("No operating observations yet")).toBeVisible();
  await expect(page.getByText("Awaiting revenue data")).toBeVisible();
  await expect(page.getByText("No pending decisions")).toBeVisible();
  await expect(page.getByText("$12,500")).toHaveCount(0);
});

test("keeps other sections usable when one backend view fails", async ({ page, request }) => {
  await request.post("http://127.0.0.1:4100/__scenario/partial");
  await page.goto("/dashboard");
  await expect(page.getByText("Section unavailable")).toBeVisible();
  await expect(page.getByText("Customer-backed opportunity ready")).toBeVisible();
  await expect(page.getByText("Review contribution margin risk")).toBeVisible();
});
