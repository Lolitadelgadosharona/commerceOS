import { expect, test } from "@playwright/test";

const productId = "53535353-5353-4353-8353-535353535353";
test.beforeEach(async ({ request }) => { await request.post("http://127.0.0.1:4100/__scenario/success"); });

test("Shopify Control Center exposes governed connection", async ({ page }) => {
  await page.goto("/channels/shopify");
  await expect(page.getByRole("heading", { name: "Shopify Control Center" })).toBeVisible();
  await expect(page.getByText("GraphQL Admin 2026-07")).toBeVisible();
  await expect(page.getByText("read_products, write_products").first()).toBeVisible();
});

test("Shopify product workspace shows projection and boundaries", async ({ page }) => {
  await page.goto(`/channels/shopify/${productId}`);
  await expect(page.getByRole("heading", { name: "Shopify Projection" })).toBeVisible();
  await expect(page.getByText("NONE — never fabricated")).toBeVisible();
  await expect(page.getByText("APPROVAL ≠ EXECUTION · EXECUTION ≠ TRAFFIC")).toBeVisible();
});

test("Listing links to governed Shopify workspace", async ({ page }) => {
  await page.goto(`/listings/${productId}`);
  await expect(page.getByRole("heading", { name: "Shopify Readiness Projection" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Open governed Shopify workspace →" })).toHaveAttribute("href", `/channels/shopify/${productId}`);
});
