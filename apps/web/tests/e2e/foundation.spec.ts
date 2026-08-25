import { expect, test } from "@playwright/test";

test("renders the foundation shell", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Commerce OS Control Center" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link", { name: /Opportunities/ })).toBeVisible();
  await page.goto("/opportunities");
  await expect(page.getByRole("heading", { name: "Opportunity workspace" })).toBeVisible();
  await expect(page.getByText("Commerce OS Opportunity APIs")).toBeVisible();
});
