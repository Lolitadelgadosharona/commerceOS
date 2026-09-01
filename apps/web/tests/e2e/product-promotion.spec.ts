import {
  expect,
  test,
  type APIRequestContext,
  type Page,
} from "@playwright/test";

const hypothesisId = "31313131-3131-4131-8131-313131313131";
const opportunityId = "77777777-7777-4777-8777-777777777777";

async function promotionScenario(request: APIRequestContext) {
  await request.post("http://127.0.0.1:4100/__scenario/promotion");
}

async function openReadyProduct(page: Page, request: APIRequestContext) {
  await promotionScenario(request);
  await page.goto(`/products/${hypothesisId}`);
}

test("1 approved opportunity shows Product Promotion section", async ({
  page,
  request,
}) => {
  await promotionScenario(request);
  await page.goto(`/opportunities/${opportunityId}?kind=market`);
  await expect(
    page.getByRole("heading", {
      name: "Opportunity Approved ≠ Product Created",
    }),
  ).toBeVisible();
});

test("2 hypothesis promotion readiness is visible", async ({
  page,
  request,
}) => {
  await openReadyProduct(page, request);
  await expect(
    page.getByRole("heading", { name: "Separate promotion decision" }),
  ).toBeVisible();
  await expect(page.getByText("READY", { exact: true }).first()).toBeVisible();
});

test("3 readiness warnings are explicit", async ({ page, request }) => {
  await openReadyProduct(page, request);
  await expect(
    page.getByText(
      "Economic value exists but source provenance is not established.",
    ),
  ).toBeVisible();
});

test("4 founder can request promotion", async ({ page, request }) => {
  await openReadyProduct(page, request);
  await page
    .getByLabel("Promotion reason")
    .fill("Evidence supports a governed Product draft.");
  await page.getByRole("button", { name: "Request Product Promotion" }).click();
  await expect(
    page.getByText(
      "Product promotion entered its own governed approval workflow.",
    ),
  ).toBeVisible();
});

test("5 promotion has a distinct approval workflow", async ({
  page,
  request,
}) => {
  await openReadyProduct(page, request);
  await page
    .getByLabel("Promotion reason")
    .fill("Request separate promotion review.");
  await page.getByRole("button", { name: "Request Product Promotion" }).click();
  await expect(
    page.getByText("pending", { exact: true }).first(),
  ).toBeVisible();
});

test("6 promotion reason is required", async ({ page, request }) => {
  await openReadyProduct(page, request);
  await expect(page.getByLabel("Promotion reason")).toHaveAttribute(
    "required",
    "",
  );
});

test("7 investment approval does not create Product", async ({
  page,
  request,
}) => {
  await openReadyProduct(page, request);
  await expect(
    page.getByText("NOT STARTED", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Create governed Product" }),
  ).toHaveCount(0);
});

test("8 promoted Product action appears only after promotion approval", async ({
  page,
  request,
}) => {
  await promotionScenario(request);
  await request.post("http://127.0.0.1:4100/__promotion/approve");
  await page.goto(`/products/${hypothesisId}`);
  await expect(
    page.getByRole("button", { name: "Create governed Product" }),
  ).toBeVisible();
});

test("9 Product retains originating Hypothesis", async ({ page, request }) => {
  await promotionScenario(request);
  await request.post("http://127.0.0.1:4100/__promotion/create-product");
  await page.goto(`/products/${hypothesisId}`);
  await expect(
    page.getByRole("heading", { name: "Portable pet cooling mat" }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "The canonical Product relationship is recorded through the governed promotion.",
    ),
  ).toBeVisible();
});

test("10 Product retains originating Opportunity", async ({
  page,
  request,
}) => {
  await promotionScenario(request);
  await request.post("http://127.0.0.1:4100/__promotion/create-product");
  await page.goto(`/products/${hypothesisId}`);
  await expect(
    page.getByRole("link", { name: "Source opportunity →" }),
  ).toHaveAttribute("href", new RegExp(opportunityId));
});

test("11 Product Truth draft action is visible after Product creation", async ({
  page,
  request,
}) => {
  await promotionScenario(request);
  await request.post("http://127.0.0.1:4100/__promotion/create-product");
  await page.goto(`/products/${hypothesisId}`);
  await expect(
    page.getByRole("button", { name: "Create Product Truth Draft" }),
  ).toBeVisible();
});

test("12 Product Truth approval remains a separate stage", async ({
  page,
  request,
}) => {
  await promotionScenario(request);
  await request.post("http://127.0.0.1:4100/__promotion/create-product");
  await page.goto(`/products/${hypothesisId}`);
  await expect(
    page.getByText("Product Truth", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page.getByText("NOT STARTED", { exact: true }).first(),
  ).toBeVisible();
});

test("13 Hypothesis versus Truth comparison renders compatible fields", async ({
  page,
  request,
}) => {
  await promotionScenario(request);
  await request.post("http://127.0.0.1:4100/__promotion/create-product");
  await page.goto(`/products/${hypothesisId}`);
  await expect(page.getByText("product name")).toBeVisible();
  await expect(page.getByText(/Hypothesis:/).first()).toBeVisible();
});

test("14 legacy economics provenance warning appears", async ({
  page,
  request,
}) => {
  await openReadyProduct(page, request);
  await expect(page.getByText("legacy economics provenance")).toBeVisible();
});

test("15 known provenance displays source and confidence", async ({
  page,
  request,
}) => {
  await openReadyProduct(page, request);
  await expect(page.getByText(/QUOTED · supplier quote · 90%/)).toBeVisible();
});

test("16 unknown economic values remain UNKNOWN", async ({ page, request }) => {
  await openReadyProduct(page, request);
  await expect(page.getByText("UNKNOWN", { exact: true })).toBeVisible();
});

test("17 lifecycle states render from hypothesis to commerce", async ({
  page,
  request,
}) => {
  await openReadyProduct(page, request);
  await expect(
    page.getByText("Product Hypothesis", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Commerce Readiness", { exact: true }),
  ).toBeVisible();
});

test("18 Product workflow exposes no Shopify execution", async ({
  page,
  request,
}) => {
  await openReadyProduct(page, request);
  await expect(
    page.getByRole("button", { name: /Shopify|Publish listing/i }),
  ).toHaveCount(0);
});

test("19 Growth workspace regression remains available", async ({
  page,
  request,
}) => {
  await request.post("http://127.0.0.1:4100/__scenario/growth");
  await page.goto("/growth");
  await expect(page.getByRole("heading", { name: "Growth OS" })).toBeVisible();
});

test("20 Sprint 071 Committee Packet regression preserves two decisions", async ({
  page,
  request,
}) => {
  await promotionScenario(request);
  await page.goto(`/decision-committee/${opportunityId}`);
  await expect(
    page.getByText("Investment Decision", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Product Promotion Decision", { exact: true }),
  ).toBeVisible();
});
