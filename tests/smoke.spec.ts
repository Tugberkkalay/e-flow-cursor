import { expect, test } from "@playwright/test";

test("clone template, run instance, and verify exports/timeline", async ({
  page,
  request,
}) => {
  await page.goto("/design");
  await expect(page.getByText("Design Studio")).toBeVisible();

  await page
    .getByRole("button", { name: "Create from template" })
    .first()
    .click();
  await expect(page.getByText(/Template cloned:/)).toBeVisible();

  await page.getByRole("button", { name: "Yayinla" }).click();
  await expect(page.getByText(/Published v/)).toBeVisible();

  await page.goto("/processes");
  await page.getByRole("button", { name: "Surec Baslat" }).click();

  const flowSelect = page.locator("select").last();
  const options = await flowSelect.locator("option").evaluateAll((items) =>
    items.map((item) => ({
      value: (item as HTMLOptionElement).value,
      text: item.textContent ?? "",
    })),
  );
  const target = options.find((option) => option.text.includes("Clone")) ?? options[0];
  await flowSelect.selectOption(target.value);

  await page.getByRole("button", { name: "Start instance" }).click();
  await page.waitForURL(/\/processes\/.+/);
  await expect(page.getByText("instance.started")).toBeVisible();

  const instanceId = page.url().split("/").pop();
  expect(instanceId).toBeTruthy();

  const login = await request.post("http://127.0.0.1:8000/auth/login", {
    data: {
      email: "admin@eflow.local",
      password: "admin123",
    },
  });
  expect(login.ok()).toBeTruthy();
  const auth = (await login.json()) as { access_token: string };
  const detail = await request.get(`http://127.0.0.1:8000/instances/${instanceId}`, {
    headers: {
      Authorization: `Bearer ${auth.access_token}`,
    },
  });
  const instance = (await detail.json()) as {
    active_tasks?: Array<{ id: string }>;
  };
  const taskId = instance.active_tasks?.[0]?.id;
  expect(taskId).toBeTruthy();

  const complete = await request.post(
    `http://127.0.0.1:8000/tasks/${taskId}/complete`,
    {
      headers: {
        Authorization: `Bearer ${auth.access_token}`,
      },
      data: {
        outcome: "submitted",
        payload: {
          request_title: "Playwright PR",
          request_type: "Standart",
          department: "Operations",
          budget_type: "default",
          currency: "TRY",
          vat_rate: 0,
          line_items: [{ item_name: "Laptop", quantity: 1, unit_price: 12000 }],
        },
      },
    },
  );
  expect(complete.ok()).toBeTruthy();

  await page.goto(`/processes/${instanceId}`);
  await page.getByRole("tab", { name: "Controls / Flags" }).click();
  await expect(page.locator("pre").nth(1)).toContainText("total_amount");

  await page.getByRole("tab", { name: "Timeline" }).click();
  await expect(page.getByText("node.completed").first()).toBeVisible();
});
