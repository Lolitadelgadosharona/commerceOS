import { expect, test } from "@playwright/test";

test("renders an honest Growth OS founder workspace", async ({ page }) => {
  await page.goto("/growth");
  await expect(page.getByRole("heading", { name: "Turn evidence into the next right action." })).toBeVisible();
  await expect(page.getByText("No Growth workspace yet.")).toBeVisible();
  await expect(page.getByText("No external Email connector configured — manual send mode active")).toBeVisible();
  await expect(page.getByText("Actual revenue", { exact: true })).toBeVisible();
  await expect(page.getByText("Actual cost", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Growth OS is usable" })).toBeVisible();
  await expect(page.getByText("Cost evidence missing")).toBeVisible();
});

test("operates a prospect workspace without UUID entry or external sending", async ({ page, request }) => {
  await request.post("http://127.0.0.1:4100/__scenario/growth");
  await page.goto("/growth/20202020-2020-4020-8020-202020202020");
  await expect(page.getByRole("heading", { name: "Rose & Brow Studio" })).toBeVisible();
  await expect(page.getByText("System next action")).toBeVisible();
  await expect(page.getByText("Create diagnosis", { exact: true })).toBeVisible();
  await page.getByText("Compose opportunity and diagnosis").click();
  await expect(page.getByText("Booking action is not visible on the service page.").first()).toBeVisible();
  await expect(page.getByText("1 of 1 selected").first()).toBeVisible();
  await expect(page.getByText("manual send mode active", { exact: false })).toBeVisible();
  await expect(page.locator('input[placeholder*="-"]')).toHaveCount(0);
});
