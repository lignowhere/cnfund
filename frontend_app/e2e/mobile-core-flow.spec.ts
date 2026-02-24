import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

test.describe.configure({ mode: "serial" });

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Tên đăng nhập").fill("admin");
  await page.getByLabel("Mật khẩu").fill("1997");
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
}

test("mobile login and bottom navigation", async ({ page }) => {
  await login(page);

  await expect(page.getByRole("heading", { name: "Tổng quan" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Giao dịch" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Nhà đầu tư" })).toBeVisible();

  await page.getByRole("link", { name: "Giao dịch" }).click();
  await expect(page).toHaveURL(/\/transactions$/);
  await expect(page.getByText("Thêm giao dịch / cập nhật NAV")).toBeVisible();
});

test("create investor from mobile flow", async ({ page }) => {
  const uniqueName = `E2E NDT ${Date.now()}`;

  await login(page);
  await page.getByRole("link", { name: "Nhà đầu tư" }).click();
  await expect(page).toHaveURL(/\/investors$/);

  await page.getByPlaceholder("Tên").fill(uniqueName);
  await page.getByPlaceholder("Số điện thoại").fill("0900000000");
  await page.getByPlaceholder("Email").fill("e2e@example.com");
  await page.getByPlaceholder("Địa chỉ chi tiết (số nhà, đường...)").fill("TP HCM");
  await page.getByRole("button", { name: "Tạo nhà đầu tư" }).click();

  await expect(page.getByText("Đã tạo nhà đầu tư mới.")).toBeVisible();
  await expect(page.getByText(uniqueName)).toBeVisible();
});

test("create nav update transaction and see card list", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Giao dịch" }).click();
  await expect(page).toHaveURL(/\/transactions$/);

  await page.locator("select").first().selectOption("nav_update");
  await page.getByPlaceholder("Tổng NAV sau giao dịch").fill("100000000");
  await page.getByRole("button", { name: "Thực hiện" }).click();

  await expect(page.getByText("Đã cập nhật giao dịch thành công.")).toBeVisible();
  await expect(page.getByText("Lịch sử giao dịch")).toBeVisible();
});

test("fee preview renders result cards on mobile", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Phí" }).click();
  await expect(page).toHaveURL(/\/fees$/);

  await page.getByPlaceholder("2,500,000,000").fill("100000000");
  await page.getByRole("button", { name: "Xem trước" }).click();

  await expect(page.getByText("Kết quả xem trước")).toBeVisible();
  await expect(page.locator("text=Phí:").first()).toBeVisible();
  await expect(page.locator("text=Config áp dụng:").first()).toBeVisible();
});

test("fee apply requires both acknowledgements", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Phí" }).click();
  await expect(page).toHaveURL(/\/fees$/);

  await page.getByPlaceholder("2,500,000,000").fill("100000000");
  await page.getByRole("button", { name: "Xem trước" }).click();

  const applyButton = page.getByRole("button", { name: "Áp dụng phí" });
  await expect(applyButton).toBeDisabled();

  await page
    .locator('label:has-text("chấp nhận rủi ro ghi phí") input[type="checkbox"]')
    .check();
  await expect(applyButton).toBeDisabled();

  await page.locator('label:has-text("đảm bảo có bản sao lưu") input[type="checkbox"]').check();
  await expect(applyButton).toBeEnabled();
});

test("backup restore requires RESTORE phrase", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: "Mở menu" }).click();
  await page.getByRole("link", { name: "Sao lưu" }).click();
  await expect(page).toHaveURL(/\/backup$/);

  await page.getByRole("button", { name: "Tạo sao lưu thủ công" }).click();
  await expect(page.getByText("Đã tạo bản sao lưu thành công:")).toBeVisible();

  await page.getByRole("button", { name: "Khôi phục" }).first().click();

  const confirmRestoreButton = page.getByRole("button", { name: "Xác nhận khôi phục" });
  await expect(confirmRestoreButton).toBeDisabled();

  await page.getByPlaceholder("Nhập RESTORE").fill("RESTORE");
  await expect(confirmRestoreButton).toBeEnabled();
});

test("open reports page from drawer", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: "Mở menu" }).click();
  await page.getByRole("link", { name: "Báo cáo" }).click();
  await expect(page).toHaveURL(/\/reports$/);
  await expect(page.getByRole("heading", { name: "Báo cáo giao dịch" })).toBeVisible();
});
