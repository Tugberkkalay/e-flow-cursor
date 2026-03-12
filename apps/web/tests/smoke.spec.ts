import { expect, test } from "@playwright/test";

test("template to instance flow smoke", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByText("Domain Template Galerisi")).toBeVisible();

  await page.goto("/processes");
  await expect(page.getByText("Süreç Başlat")).toBeVisible();
  await page.getByText("Süreç Başlat").click();
  await expect(page.getByText("Published flow seçin")).toBeVisible();
  await page.getByRole("button", { name: "Başlat (MVP)" }).click();
  await expect(page.getByText("PR - Office Equipment")).toBeVisible();

  await page.goto("/processes/ins_1001");
  await expect(page.getByRole("tab", { name: "Timeline" })).toBeVisible();
  await expect(page.getByText("instance.started")).toBeVisible();
});
