import { test, expect } from '@playwright/test';
import { writeFileSync, readFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

test.describe.configure({ mode: 'serial' });

test.describe('File Operations', () => {
  test.beforeEach(async ({ page }) => {
    // Capture console messages
    page.on('console', (msg) => {
      console.log(`[Browser Console ${msg.type()}]:`, msg.text());
    });

    // Capture network requests
    page.on('request', (request) => {
      console.log(`[Request] ${request.method()} ${request.url()}`);
    });

    page.on('response', async (response) => {
      const url = response.url();
      const status = response.status();
      console.log(`[Response] ${status} ${url}`);

      // Log API responses
      if (url.includes('/api/')) {
        try {
          const body = await response.text();
          console.log(`[Response Body] ${url}:`, body.substring(0, 500));
        } catch (e) {
          console.log(`[Response Body] ${url}: Could not read body`);
        }
      }
    });

    // Capture page errors
    page.on('pageerror', (error) => {
      console.log(`[Page Error]:`, error.message);
    });

    // Capture failed requests
    page.on('requestfailed', (request) => {
      console.log(
        `[Request Failed] ${request.url()}:`,
        request.failure()?.errorText
      );
    });
  });

  test('should upload a PDF file successfully', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Debug: Take screenshot and log page content
    await page.screenshot({
      path: 'test-results/debug-page-load.png',
      fullPage: true,
    });
    const bodyText = await page.locator('body').textContent();
    console.log('Page body text:', bodyText);

    // Check if there's an error message
    const errorElement = page.locator('.text-red-800, [class*="error"]');
    if ((await errorElement.count()) > 0) {
      const errorText = await errorElement.first().textContent();
      console.log('Error found on page:', errorText);
    }

    const timestamp = Date.now();
    const filename = `test-upload-${timestamp}.pdf`;

    // Use the test PDF file
    const testPdfPath = join(__dirname, 'fixtures', 'test-document.pdf');
    const testFilePath = join(tmpdir(), filename);

    // Copy the PDF content to a temp file with timestamp name
    const pdfContent = readFileSync(testPdfPath);
    writeFileSync(testFilePath, pdfContent);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    await page.waitForTimeout(2000);

    await expect(page.getByText(/uploaded.*1 file/i)).toBeVisible({
      timeout: 5000,
    });

    const fileCard = page.locator('.bg-white').filter({ hasText: filename });
    await expect(fileCard).toBeVisible();
  });

  test('should reject non-PDF file upload', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const timestamp = Date.now();
    const filename = `test-reject-${timestamp}.txt`;
    const testContent = 'This is a text file that should be rejected.';
    const testFilePath = join(tmpdir(), filename);
    writeFileSync(testFilePath, testContent);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    await page.waitForTimeout(2000);

    // Should show error message for non-PDF file
    await expect(page.getByText(/only pdf files are allowed/i)).toBeVisible({
      timeout: 5000,
    });

    // File should not appear in the list
    const fileCard = page.locator('.bg-white').filter({ hasText: filename });
    await expect(fileCard).not.toBeVisible();
  });

  test('should reject fake PDF file (wrong content)', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const timestamp = Date.now();
    const filename = `fake-pdf-${timestamp}.pdf`;
    const fakeContent =
      'This is not a real PDF file, just text with .pdf extension';
    const testFilePath = join(tmpdir(), filename);
    writeFileSync(testFilePath, fakeContent);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    await page.waitForTimeout(2000);

    // Should show error message for fake PDF
    await expect(
      page.getByText(/not a valid pdf|pdf validation failed/i)
    ).toBeVisible({ timeout: 5000 });

    // File should not appear in the list
    const fileCard = page.locator('.bg-white').filter({ hasText: filename });
    await expect(fileCard).not.toBeVisible();
  });

  test('should rename a folder', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const timestamp = Date.now();
    const originalName = `TestFolder-${timestamp}`;
    const newName = `RenamedFolder-${timestamp}`;

    const newFolderButton = page.getByRole('button', { name: /new folder/i });
    await newFolderButton.click();

    const input = page.getByPlaceholder(/folder name/i);
    await input.fill(originalName);

    const createButton = page.getByRole('button', { name: /create/i });
    await createButton.click();

    await page.waitForTimeout(1000);

    const folderCard = page
      .locator('.bg-white')
      .filter({ hasText: originalName })
      .first();
    await expect(folderCard).toBeVisible();

    // Scroll the folder card into view to ensure it's visible
    await folderCard.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);

    const renameButton = folderCard.getByRole('button', { name: 'Rename' });
    await expect(renameButton).toBeVisible();
    await renameButton.click();

    // Wait for React state to update and component to re-render
    await page.waitForTimeout(1000);

    // Wait for the rename input field to appear
    const renameInput = page.locator('input[type="text"]').first();
    await expect(renameInput).toBeVisible({ timeout: 10000 });
    await renameInput.waitFor({ state: 'attached' });

    // Clear and fill the new name (don't verify current value, just replace it)
    await renameInput.click();
    await renameInput.fill(newName);
    await renameInput.press('Enter');

    // Wait for the rename operation to complete
    await page.waitForTimeout(1000);

    // Check that the renamed folder card is visible
    const renamedFolderCard = page
      .locator('.bg-white')
      .filter({ hasText: newName })
      .first();
    await expect(renamedFolderCard).toBeVisible({ timeout: 10000 });

    // Check that the original name is no longer visible
    await expect(
      page.locator('.bg-white').filter({ hasText: originalName })
    ).not.toBeVisible();
  });

  test('should rename a file', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const timestamp = Date.now();
    const originalName = `original-name-${timestamp}.pdf`;
    const newName = `new-filename-${timestamp}.pdf`;

    // Use the test PDF file
    const testPdfPath = join(__dirname, 'fixtures', 'test-document.pdf');
    const testFilePath = join(tmpdir(), originalName);
    const pdfContent = readFileSync(testPdfPath);
    writeFileSync(testFilePath, pdfContent);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    await page.waitForTimeout(1500);

    const fileCard = page
      .locator('.bg-white')
      .filter({ hasText: originalName })
      .first();
    await expect(fileCard).toBeVisible();

    // Scroll the file card into view
    await fileCard.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);

    const renameButton = fileCard.getByRole('button', { name: 'Rename' });
    await expect(renameButton).toBeVisible();
    await renameButton.click();

    // Wait for React state to update
    await page.waitForTimeout(1000);

    // Wait for the rename input field to appear
    const renameInput = page.locator('input[type="text"]').first();
    await expect(renameInput).toBeVisible({ timeout: 10000 });
    await renameInput.waitFor({ state: 'attached' });

    // Clear and fill the new name
    await renameInput.click();
    await renameInput.fill(newName);
    await renameInput.press('Enter');

    // Wait for the rename operation to complete
    await page.waitForTimeout(1000);

    // Check that the renamed file card is visible
    const renamedFileCard = page
      .locator('.bg-white')
      .filter({ hasText: newName })
      .first();
    await expect(renamedFileCard).toBeVisible({ timeout: 10000 });

    // Check that the original name is no longer visible
    await expect(
      page.locator('.bg-white').filter({ hasText: originalName })
    ).not.toBeVisible();
  });

  test('should delete a file', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const timestamp = Date.now();
    const filename = `file-to-delete-${timestamp}.pdf`;

    // Use the test PDF file
    const testPdfPath = join(__dirname, 'fixtures', 'test-document.pdf');
    const testFilePath = join(tmpdir(), filename);
    const pdfContent = readFileSync(testPdfPath);
    writeFileSync(testFilePath, pdfContent);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    await page.waitForTimeout(1000);

    const fileCard = page
      .locator('.bg-white')
      .filter({ hasText: filename })
      .first();
    await expect(fileCard).toBeVisible();

    const deleteButton = fileCard.getByRole('button', { name: 'Delete' });
    await deleteButton.click();

    await page.waitForTimeout(300);

    const modal = page
      .getByRole('dialog')
      .or(page.locator('[role="dialog"]'))
      .or(page.locator('.fixed.inset-0'));
    await expect(modal.getByText('Delete Item')).toBeVisible();

    const confirmButton = modal.getByRole('button', {
      name: 'Delete',
      exact: true,
    });
    await confirmButton.click();

    await page.waitForTimeout(500);

    await expect(page.getByText(/deleted successfully/i)).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText(filename)).not.toBeVisible();
  });
});
