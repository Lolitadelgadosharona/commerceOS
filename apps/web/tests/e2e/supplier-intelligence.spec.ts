import { expect, test } from "@playwright/test";

const supplierId = "63636363-6363-4363-8363-636363636363";

test("supplier navigation opens the governed workspace", async ({ page }) => {
  await page.goto("/suppliers");
  await expect(page.getByRole("heading", { name: "Supplier Intelligence" })).toBeVisible();
  await expect(page.getByText("selection only · no purchase")).toBeVisible();
});

test("supplier workspace uses canonical profiles and Product matches", async ({ page }) => {
  await page.goto("/suppliers");
  await expect(page.getByRole("heading", { name: "Atlantic Care Manufacturing" })).toBeVisible();
  await expect(page.getByText("Cooling textiles · Private label packaging")).toBeVisible();
});

test("supplier detail exposes explainable qualification dimensions", async ({ page }) => {
  await page.goto(`/suppliers/${supplierId}`);
  await expect(page.getByRole("heading", { name: "Qualification dashboard" })).toBeVisible();
  await expect(page.getByText("product fit")).toBeVisible();
  await expect(page.getByText("compliance", { exact: true })).toBeVisible();
});

test("supplier detail distinguishes claimed evidence from quotes", async ({ page }) => {
  await page.goto(`/suppliers/${supplierId}`);
  await expect(page.getByText("supplier_claimed", { exact: true })).toBeVisible();
  await expect(page.getByText("USD 11.5000")).toBeVisible();
  await expect(page.getByText(/MOQ 100/)).toBeVisible();
});

test("supplier detail preserves approval and purchase boundary", async ({ page }) => {
  await page.goto(`/suppliers/${supplierId}`);
  await expect(page.getByRole("heading", { name: "Selection status" })).toBeVisible();
  await expect(page.getByText(/No governed Product-Supplier selection exists/)).toBeVisible();
  await expect(page.getByRole("link", { name: "Decision Committee", exact: true })).toBeVisible();
});

test("6 supplier detail shows the linked Product without name inference", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByRole("heading", { name: "Linked Products" })).toBeVisible(); await expect(page.getByText(/Product 53535353/).first()).toBeVisible(); });
test("7 Product Truth requirement gap remains explicit", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText(/Verify compliance evidence against current Product Truth/).first()).toBeVisible(); });
test("8 provenance retains the original source", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText("supplier questionnaire", { exact: true })).toBeVisible(); });
test("9 unknown tooling cost remains UNKNOWN", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText(/Tooling UNKNOWN/)).toBeVisible(); });
test("10 known numeric zero remains zero", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText(/Packaging 0.0000/)).toBeVisible(); });
test("11 qualification readiness renders", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText("READY FOR REVIEW")).toBeVisible(); });
test("12 missing supplier risk records do not become zero risk", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText(/not proof of zero risk/)).toBeVisible(); });
test("13 comparison context shows the persisted match score", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText("84 fit")).toBeVisible(); });
test("14 no fabricated weighted supplier total appears", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText(/weighted total/i)).toHaveCount(0); });
test("15 qualification warning is visible", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText("unknown", { exact: true })).toBeVisible(); });
test("16 qualified supplier can request governed approval", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByRole("button", { name: "Request supplier approval" })).toBeVisible(); });
test("17 supplier request enters the human decision workflow", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await page.getByPlaceholder(/Explain why this supplier/).fill("Evidence supports primary supplier review."); await page.getByRole("button", { name: "Request supplier approval" }).click(); await expect(page.getByText(/entered human review/)).toBeVisible(); });
test("18 approval action explicitly excludes supplier execution", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText(/never sends, orders, negotiates, or pays/)).toBeVisible(); });
test("19 approved relationship is not fabricated", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText(/No governed Product-Supplier selection exists/)).toBeVisible(); });
test("20 deterministic next action is visible", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText(/Verify compliance evidence against current Product Truth/).first()).toBeVisible(); });
test("21 supplier capabilities render from persisted data", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText(/Cooling textiles/)).toBeVisible(); });
test("22 supplier certification metadata renders", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText("ISO 9001")).toBeVisible(); });
test("23 supplier source classification renders", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText(/manufacturer · Portugal/i)).toBeVisible(); });
test("24 Product traceability uses the canonical Product identifier", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByText("Product 53535353-5353-4353-8353-535353535353").first()).toBeVisible(); });
test("25 Decision Committee remains the approval authority", async ({ page }) => { await page.goto(`/suppliers/${supplierId}`); await expect(page.getByRole("link", { name: "Decision Committee", exact: true })).toHaveAttribute("href", "/decision-committee"); });
