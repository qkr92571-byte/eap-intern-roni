import { test, expect } from '@playwright/test';

test.describe('공고 목록 페이지', () => {

  test('앱이 정상 로드된다', async ({ page }) => {
    await page.goto('/');
    // 로그인 페이지 또는 메인 페이지가 로드되어야 함
    await expect(page).toHaveURL(/\/(login.*|$)/);
  });

  test('로그인 페이지에 이메일/비밀번호 입력 필드가 있다', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('로그인 폼 제출 버튼이 존재한다', async ({ page }) => {
    await page.goto('/login');
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();
  });

});
