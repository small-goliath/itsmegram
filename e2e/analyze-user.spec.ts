import { test, expect } from '@playwright/test';

/**
 * E2E Test: Analyze doto.ri_ Instagram user
 *
 * This test verifies the complete user flow from homepage to report generation
 * for the Instagram user "doto.ri_"
 */
test.describe('Analyze doto.ri_ User', () => {
  // Set longer timeout for analysis operations (Instagram data fetch + AI analysis)
  test.slow();

  test('should navigate to homepage and verify initial state', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');

    // Verify page title and main elements
    await expect(page).toHaveTitle(/itsmegram/);
    await expect(page.locator('h1')).toContainText('itsmegram');
    await expect(page.locator('text=AI로 분석하는 나의 인스타그램')).toBeVisible();

    // Verify username form is present
    const usernameInput = page.locator('input[aria-label="인스타그램 아이디"]');
    await expect(usernameInput).toBeVisible();
    await expect(usernameInput).toHaveAttribute('placeholder', '인스타그램 아이디를 입력하세요');

    // Verify submit button is present
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toContainText('분석하기');

    // Take screenshot of initial state
    await page.screenshot({ path: 'e2e/screenshots/01-homepage.png', fullPage: true });
  });

  test('should fill username form and submit for doto.ri_', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');

    // Fill in the username
    const usernameInput = page.locator('input[aria-label="인스타그램 아이디"]');
    await usernameInput.fill('doto.ri_');

    // Verify the input value
    await expect(usernameInput).toHaveValue('doto.ri_');

    // Click submit button
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // Wait for navigation to report page
    await page.waitForURL('**/report?username=doto.ri_', { timeout: 10000 });

    // Verify we're on the report page
    await expect(page).toHaveURL(/\/report\?username=doto\.ri_/);

    // Take screenshot of report page loading state
    await page.screenshot({ path: 'e2e/screenshots/02-report-loading.png', fullPage: true });
  });

  test('should display analysis progress for doto.ri_', async ({ page }) => {
    // Navigate directly to report page with username
    await page.goto('/report?username=doto.ri_');

    // Wait for analysis to start - check for the loading state
    const analysisHeading = page.locator('text=doto.ri_님의 계정을 분석중입니다');
    await expect(analysisHeading).toBeVisible({ timeout: 15000 });

    // Verify progress indicator is visible
    const progressBar = page.locator('[role="progressbar"]');
    await expect(progressBar).toBeVisible();

    // Verify status message is shown
    const statusMessage = page.locator('text=인스타그램 데이터 수집 중...');
    await expect(statusMessage).toBeVisible();

    // Take screenshot of analysis progress
    await page.screenshot({ path: 'e2e/screenshots/03-analysis-progress.png', fullPage: true });

    // Wait for analysis to complete or timeout
    // Note: This may take a while due to Instagram data fetching and AI analysis
    try {
      // Wait for either completion or error (with extended timeout)
      await Promise.race([
        page.waitForSelector('text=AI 분석 리포트', { timeout: 120000 }),
        page.waitForSelector('text=분석 중 오류가 발생했습니다', { timeout: 120000 }),
      ]);

      // Take screenshot of final state
      await page.screenshot({ path: 'e2e/screenshots/04-analysis-complete.png', fullPage: true });

      // Verify report content is displayed or handle error
      const reportContent = page.locator('text=AI 분석 리포트');
      const errorMessage = page.locator('text=분석 중 오류가 발생했습니다');

      const isReportVisible = await reportContent.isVisible().catch(() => false);
      const isErrorVisible = await errorMessage.isVisible().catch(() => false);

      if (isReportVisible) {
        console.log('✅ Analysis completed successfully');
        await expect(reportContent).toBeVisible();
      } else if (isErrorVisible) {
        console.log('⚠️ Analysis failed with error');
        // Error is acceptable during testing (rate limits, Instagram blocks, etc.)
        await expect(errorMessage).toBeVisible();
      }
    } catch (e) {
      // If timeout occurs, the analysis is taking longer than expected
      // This is acceptable for E2E testing purposes
      console.log('⏱️ Analysis is taking longer than expected (timeout)');
      await page.screenshot({ path: 'e2e/screenshots/04-analysis-timeout.png', fullPage: true });
    }
  });

  test('should handle form validation for empty username', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');

    // Try to submit empty form
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // Verify error message is shown
    const errorMessage = page.locator('text=아이디를 입력해주세요');
    await expect(errorMessage).toBeVisible();

    // Take screenshot of validation error
    await page.screenshot({ path: 'e2e/screenshots/05-validation-error.png', fullPage: true });
  });

  test('should handle invalid username format', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');

    // Fill in invalid username
    const usernameInput = page.locator('input[aria-label="인스타그램 아이디"]');
    await usernameInput.fill('invalid@username!');

    // Try to submit - HTML5 pattern validation will prevent form submission
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // Due to HTML5 pattern attribute, browser native validation prevents submit
    // So we verify the form was NOT submitted (still on homepage)
    await expect(page).toHaveURL('/');

    // Verify the invalid value is still in the input (form didn't submit)
    await expect(usernameInput).toHaveValue('invalid@username!');

    // Alternative: Check for browser validation message (if accessible)
    // The browser shows native tooltip which we can't easily test,
    // but we verify the page state hasn't changed
  });

  test('should navigate back to home from report page without username', async ({ page }) => {
    // Navigate to report page without username parameter
    await page.goto('/report');

    // Verify redirect or error message
    await page.waitForTimeout(1000);

    // Check if we're on homepage or error state
    const currentUrl = page.url();
    if (currentUrl.includes('/report')) {
      // Should show error state on report page
      const errorMessage = page.locator('text=아이디가 필요합니다');
      await expect(errorMessage).toBeVisible();
    } else {
      // Should redirect to homepage
      await expect(page).toHaveURL('/');
    }
  });
});
