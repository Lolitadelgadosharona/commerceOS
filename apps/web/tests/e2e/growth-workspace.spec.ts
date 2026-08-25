import { expect, test } from "@playwright/test";

test("renders an honest Growth OS founder workspace", async ({ page }) => {
  await page.goto("/growth");
  await expect(page.getByRole("heading", { name: "Turn evidence into the next right action." })).toBeVisible();
  await expect(page.getByText("No Growth workspace yet.")).toBeVisible();
  await expect(page.getByText("No external Email connector configured — manual send mode active")).toBeVisible();
  await expect(page.getByText("Recorded revenue")).toBeVisible();
  await expect(page.getByText("Recorded cost", { exact: true })).toBeVisible();
});
