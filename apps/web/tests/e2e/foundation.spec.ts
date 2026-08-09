import { expect, test } from "@playwright/test";

test("renders the foundation shell", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Commerce OS" })).toBeVisible();
  await expect(page.getByText("No business workflows are enabled")).toBeVisible();
});
