import { expect, test } from "@playwright/test";

test("renders the project console", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Customer AI Portal" })).toBeVisible();
  await expect(page.getByRole("button", { name: "New Scan" })).toBeVisible();
  await page.getByRole("tab", { name: "evidence" }).click();
  await expect(page.getByText("SHA-256")).toBeVisible();
});
