import { expect, test } from "@playwright/test";

const marketId = "77777777-7777-4777-8777-777777777777";
const candidateId = "88888888-8888-4888-8888-888888888888";

test.beforeEach(async ({ request }) => {
  await request.post("http://127.0.0.1:4100/__scenario/success");
});

test("maps dashboard decisions into the governed opportunity context", async ({ page }) => {
  await page.goto("/dashboard");
  await page.getByRole("link", { name: /Investment decision: Seasonal pet cooling mat/ }).click();
  await expect(page).toHaveURL(/\/opportunities\?approval=/);
  await expect(page.getByText("Decision Queue context")).toBeVisible();
  await page.getByRole("link", { name: /Evidence and economics require human investment review/ }).click();
  await expect(page).toHaveURL(new RegExp(`/opportunities/${marketId}\\?kind=market`));
});

test("renders scored opportunities without merging discovery and investment records", async ({ page }) => {
  await page.goto("/opportunities");
  await expect(page.getByRole("heading", { name: "Opportunity workspace" })).toBeVisible();
  await expect(page.getByText("Market opportunity", { exact: true })).toBeVisible();
  await expect(page.getByText("Demand candidate", { exact: true })).toBeVisible();
  await expect(page.getByText("Waiting for human decision")).toBeVisible();
  await expect(page.getByText("Marketplace validation")).toHaveCount(0);
});

test("shows the evidence-to-decision investment review and records approval", async ({ page }) => {
  await page.goto(`/opportunities/${marketId}?kind=market`);
  await expect(page.getByRole("heading", { name: "Seasonal pet cooling mat" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Evidence ledger" })).toBeVisible();
  await expect(page.getByText("Owners report pet heat discomfort during summer travel.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Economics" })).toBeVisible();
  await expect(page.getByText("Platform policy evidence requires validation.")).toBeVisible();
  await expect(page.getByText("Customer evidence is required").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Investment decision required" })).toBeVisible();

  await page.getByLabel("Decision reason").fill("Evidence supports a controlled validation step.");
  await page.getByRole("button", { name: "Approve investment" }).click();
  await expect(page.getByRole("heading", { name: "approved" })).toBeVisible();
  await expect(page.getByText("Evidence supports a controlled next step.")).toBeVisible();
});

test("keeps discovery candidates advisory and non-executable", async ({ page }) => {
  await page.goto(`/opportunities/${candidateId}?kind=candidate`);
  await expect(page.getByRole("heading", { name: "Travel hydration reminder" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Intelligence candidate—not an executable investment" })).toBeVisible();
  await expect(page.getByText("Marketplace validation")).toBeVisible();
  await expect(page.getByRole("button", { name: /Approve investment/ })).toHaveCount(0);
});

test("shows intentional empty and backend failure states", async ({ page, request }) => {
  await request.post("http://127.0.0.1:4100/__scenario/empty");
  await page.goto("/opportunities");
  await expect(page.getByText("No opportunities yet")).toBeVisible();

  await request.post("http://127.0.0.1:4100/__scenario/opportunity-error");
  await page.goto("/opportunities");
  await expect(page.getByText("Opportunity workspace unavailable")).toBeVisible();
});

test("returns explicit not-found and authorization states", async ({ page, request }) => {
  await page.goto("/opportunities/not-a-uuid?kind=market");
  await expect(page.getByRole("heading", { name: "Opportunity not found" })).toBeVisible();

  await page.goto("/opportunities/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa?kind=market");
  await expect(page.getByRole("heading", { name: "Opportunity not found" })).toBeVisible();

  await request.post("http://127.0.0.1:4100/__scenario/unauthorized");
  await page.goto("/opportunities");
  await expect(page.getByRole("heading", { name: "Operational context required" })).toBeVisible();
  await expect(page.getByText("The Commerce OS API returned 403 for /api/v1/auth/me.")).toBeVisible();
});
