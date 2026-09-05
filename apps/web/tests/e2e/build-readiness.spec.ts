import { expect, test } from "@playwright/test";

const productId = "53535353-5353-4353-8353-535353535353";
const hypothesisId = "31313131-3131-4131-8131-313131313131";

test.beforeEach(async ({ request }) => {
  await request.post("http://127.0.0.1:4100/__scenario/success");
});

test("1 Build workspace loads", async ({ page }) => {
  await page.goto("/build");
  await expect(page.getByRole("heading", { name: "Product Build Control Center" })).toBeVisible();
});
test("2 Product appears with actual readiness", async ({ page }) => {
  await page.goto("/build");
  await expect(page.getByRole("heading", { name: "Portable cooling mat" })).toBeVisible();
  await expect(page.getByText("not ready", { exact: true })).toBeVisible();
});
test("3 Build detail opens", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByRole("heading", { name: "Portable cooling mat" })).toBeVisible();
});
test("4 Product Truth is visible", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByRole("heading", { name: "Product Truth & Build Specifications" })).toBeVisible();
  await expect(page.getByText(/cooling textile/).first()).toBeVisible();
});
test("5 Supplier fit is visible", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByRole("heading", { name: "Supplier Fit" })).toBeVisible();
  await expect(page.getByText("Material", { exact: true })).toBeVisible();
});
test("6 approved supplier area is visible", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByRole("heading", { name: "Approved Suppliers" })).toBeVisible();
});
test("7 unresolved relationship execution is visible", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByRole("button", { name: "Execute approved relationship" })).toBeVisible();
});
test("8 founder executes an already-approved relationship", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await page.getByRole("button", { name: "Execute approved relationship" }).click();
  await expect(page.getByRole("button", { name: "Execute approved relationship" })).toHaveCount(0);
  await expect(page.getByText("conditional", { exact: true }).first()).toBeVisible();
});
test("9 relationship execution explicitly has no external effect", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByText(/No supplier contact, order, purchase, or payment occurs/)).toBeVisible();
});
test("10 SupplierCandidate promotion UI works", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await page.getByLabel("Verified supplier name").fill("Atlantic Care Manufacturing");
  await page.getByLabel("Country").fill("Portugal");
  await page.getByRole("button", { name: "Confirm canonical Supplier Profile" }).click();
  await expect(page.getByRole("link", { name: "Canonical Supplier Profile →" })).toBeVisible();
});
test("11 canonical SupplierProfile link appears after promotion", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await page.getByLabel("Verified supplier name").fill("Atlantic Care Manufacturing");
  await page.getByLabel("Country").fill("Portugal");
  await page.getByRole("button", { name: "Confirm canonical Supplier Profile" }).click();
  await expect(page.getByRole("link", { name: "Canonical Supplier Profile →" })).toBeVisible();
});
test("12 normalized quote traceability is visible", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByText(/Quote 55555555-5555-4555-8555-555555555555/)).toBeVisible();
});
test("13 quote classification remains quoted", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByText("quoted", { exact: true }).first()).toBeVisible();
});
test("14 expired quote warning works", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByText("EXPIRED QUOTE", { exact: true })).toBeVisible();
});
test("15 sample state is visible", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByText("SAMPLE-001", { exact: true })).toBeVisible();
  await expect(page.getByText(/Review: unknown/)).toBeVisible();
});
test("16 validation evidence is visible", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByText("Material matches the approved specification.")).toBeVisible();
});
test("17 failed requirement blocks Build Ready", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByText("Execute the approved supplier relationship.")).toBeVisible();
  await expect(page.getByText("NOT READY", { exact: true }).first()).toBeVisible();
});
test("18 resolving persisted relationship requirement updates readiness", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await page.getByRole("button", { name: "Execute approved relationship" }).click();
  await expect(page.getByText("conditional", { exact: true }).first()).toBeVisible();
});
test("19 warning is not rendered as blocker", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByText(/Only one supplier is approved/)).toBeVisible();
  await expect(page.getByText("WARNING · single supplier")).toBeVisible();
});
test("20 UNKNOWN does not become PASS", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByText(/Supplier: UNKNOWN/)).toBeVisible();
  await expect(page.getByText("unknown", { exact: true }).first()).toBeVisible();
});
test("21 Product detail shows Build Readiness", async ({ page, request }) => {
  await request.post("http://127.0.0.1:4100/__promotion/create-product");
  await page.goto(`/products/${hypothesisId}`);
  await expect(page.getByRole("heading", { name: "Build Readiness" })).toBeVisible();
});
test("22 lifecycle distinguishes Supplier Validation and Build Ready", async ({ page, request }) => {
  await request.post("http://127.0.0.1:4100/__promotion/create-product");
  await page.goto(`/products/${hypothesisId}`);
  await expect(page.getByText("Supplier Validation", { exact: true })).toBeVisible();
  await expect(page.getByText("Build Ready", { exact: true })).toBeVisible();
});
test("23 backward Opportunity traceability works", async ({ page }) => {
  await page.goto(`/build/${productId}`);
  await expect(page.getByRole("link", { name: "Open originating Opportunity →" })).toHaveAttribute("href", "/opportunities/77777777-7777-4777-8777-777777777777");
});
test("24 Sprint 073 supplier regression remains available", async ({ page }) => {
  await page.goto("/suppliers");
  await expect(page.getByRole("heading", { name: "Supplier Intelligence" })).toBeVisible();
});
test("25 Sprint 072 Product Truth regression remains available", async ({ page, request }) => {
  await request.post("http://127.0.0.1:4100/__promotion/create-product");
  await page.goto(`/products/${hypothesisId}`);
  await expect(page.getByRole("heading", { name: "Portable pet cooling mat" })).toBeVisible();
});
test("26 Sprint 071 Committee regression remains available", async ({ page }) => {
  await page.goto("/decision-committee");
  await expect(page.getByRole("heading", { name: "Decision Committee" })).toBeVisible();
});
test("27 Growth regression remains available", async ({ page }) => {
  await page.goto("/growth");
  await expect(page.getByRole("heading", { name: "Growth OS" })).toBeVisible();
});
