import { expect, test } from "@playwright/test";

test("generate from a user story and export JSON", async ({ page, request }) => {
  const health = await request.get("http://127.0.0.1:8000/api/health");
  expect(health.ok()).toBeTruthy();

  await page.goto("/generate");
  const projectName = page.getByLabel("New project name");
  if (!(await projectName.isVisible())) {
    await page.getByLabel("Project").click();
    await page.getByRole("option", { name: "Create a new project" }).click();
  }
  await page.getByLabel("New project name").fill(`Transfer ${Date.now()}`);
  await page.getByLabel("Title").fill("Transfer story");
  await page.getByTestId("content-input").fill(
    "As a customer, I want to transfer money between my accounts so that I can pay a bill.\n\nAcceptance criteria:\n1. The customer can transfer an amount between 0.01 and 10000 USD.\n2. Insufficient funds show an error.",
  );
  await page.getByTestId("generate-submit").click();
  await expect(page.getByRole("heading", { name: "Generated test cases" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Verify/ }).first()).toBeVisible();

  await page.getByRole("link", { name: "Export center" }).click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Format").click();
  await page.getByRole("option", { name: "JSON" }).click();
  await page.getByRole("button", { name: "Download" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain(".json");
});

test("capture the main screens", async ({ page, request }) => {
  const seeded = await request.post("http://127.0.0.1:8000/api/demo/seed");
  expect(seeded.ok()).toBeTruthy();
  const project = await seeded.json();
  await page.addInitScript((projectId) => {
    localStorage.setItem("selectedProjectId", projectId as string);
  }, project.id);
  await page.goto("/");
  await expect(page.getByText("Demo — Account transfer")).toBeVisible();
  await page.screenshot({ path: "../docs/screenshots/dashboard.png", fullPage: true });
  await page.goto("/analysis");
  await expect(page.getByRole("heading", { name: "Requirements analysis" })).toBeVisible();
  await page.screenshot({ path: "../docs/screenshots/analysis.png", fullPage: true });
  await page.goto("/cases");
  await expect(page.getByRole("heading", { name: "Generated test cases" })).toBeVisible();
  await page.screenshot({ path: "../docs/screenshots/test-cases.png", fullPage: true });
  await page.goto("/generate");
  await page.screenshot({ path: "../docs/screenshots/generate.png", fullPage: true });
  await page.goto("/export");
  await page.screenshot({ path: "../docs/screenshots/export.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.screenshot({ path: "../docs/screenshots/dashboard-mobile.png", fullPage: true });
});
