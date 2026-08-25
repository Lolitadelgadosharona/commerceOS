import { expect, test } from "@playwright/test";

test("renders the foundation shell", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Commerce OS Control Center" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link", { name: /Opportunities/ })).toBeVisible();
  await expect(page.getByText("No business workflows are enabled")).toHaveCount(0);

  await page.goto("/opportunities");
  await expect(page.getByRole("heading", { name: "Opportunity pipeline" })).toBeVisible();
  await expect(page.getByText("/api/v1/opportunity-candidates")).toBeVisible();
});
