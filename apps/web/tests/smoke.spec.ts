import { expect, test } from "@playwright/test";

test("runs the local console workflow", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Customer AI Portal" })).toBeVisible();

  await page.getByRole("tab", { name: "Targets" }).click();
  await page.getByLabel("Target name").fill("Demo browser flow");
  await page.getByLabel("Target endpoint").fill("http://localhost:8001/chat");
  await page.getByLabel("Target type").selectOption("browser");
  await page.getByLabel("Confirm this scope before scanning").check();
  await page.getByRole("button", { name: "Add target" }).click();
  await expect(page.locator("tr").filter({ hasText: "Demo browser flow" })).toBeVisible();

  await page.getByRole("tab", { name: "Scans" }).click();
  await page.getByLabel("Scan profile").selectOption("standard");
  await page.getByLabel("Allow standard probes against local/demo fixtures").check();
  await page.getByLabel("Confirm scope for this scan").check();
  await page.getByRole("button", { name: "Start scan" }).click();
  const newScan = page.locator(".rowCard").filter({ hasText: "standard scan for" }).first();
  await expect(newScan).toBeVisible();
  await newScan.getByRole("button", { name: "Cancel scan" }).click();
  await expect(page.getByRole("status")).toContainText("cancelled");

  await page.getByRole("tab", { name: "Evidence" }).click();
  await expect(page.getByRole("heading", { name: "Injected RAG document instruction" })).toBeVisible();
  await page.getByLabel("Admin password").fill("local-admin");
  await page.getByRole("button", { name: "Reveal raw evidence" }).click();
  await expect(page.getByText("Ignore previous rules")).toBeVisible();

  await page.getByRole("tab", { name: "Coverage" }).click();
  await expect(page.getByRole("heading", { name: "ASVS 5.0 L2" })).toBeVisible();

  await page.getByRole("button", { name: "Language" }).click();
  await expect(page.getByRole("tab", { name: "証跡" })).toBeVisible();
});

test("captures README screenshots when requested", async ({ page }) => {
  test.skip(process.env.AEGISFORGE_CAPTURE_SCREENSHOTS !== "1", "set AEGISFORGE_CAPTURE_SCREENSHOTS=1 to refresh README images");
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Customer AI Portal" })).toBeVisible();

  await page.screenshot({ path: "../../docs/assets/aegisforge-dashboard.png", fullPage: true });
  await page.getByRole("tab", { name: "Targets" }).click();
  await page.screenshot({ path: "../../docs/assets/aegisforge-new-target.png", fullPage: true });
  await page.getByRole("tab", { name: "Scans" }).click();
  await page.screenshot({ path: "../../docs/assets/aegisforge-scan-wizard.png", fullPage: true });
  await page.getByRole("tab", { name: "Evidence" }).click();
  await page.screenshot({ path: "../../docs/assets/aegisforge-evidence.png", fullPage: true });
  await page.getByRole("tab", { name: "Coverage" }).click();
  await page.screenshot({ path: "../../docs/assets/aegisforge-coverage.png", fullPage: true });
});
